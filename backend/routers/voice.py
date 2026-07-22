import asyncio
import base64
import json
import logging
import time
from typing import Dict, Optional
from fastapi import APIRouter, Depends, Request, Response, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import AsyncSessionLocal, get_db
from backend.services.conversation_service import create_conversation, generate_llm_summary
from backend.services.lead_service import save_lead
from backend.models import ConversationOutcome
from voice.agent import AgentSession
from voice.audio_services import synthesize_speech_elevenlabs, transcribe_audio_deepgram

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Voice Telephony & WebRTC/WebSocket Audio"])


# --- TWILIO TELEPHONY WEBHOOKS ---

@router.api_route("/api/twilio/incoming-call", methods=["GET", "POST"])
async def twilio_incoming_call(request: Request):
    """
    Twilio Voice webhook for inbound calls.
    Returns TwiML connecting the call to the WebSocket Media Stream.
    """
    host = request.headers.get("host", "localhost:8000")
    protocol = "wss" if "https" in str(request.base_url) or not ("localhost" in host or "127.0.0.1" in host) else "ws"
    
    # If PUBLIC_BASE_URL is configured, use its host and wss
    if settings.PUBLIC_BASE_URL and not settings.PUBLIC_BASE_URL.startswith("http://localhost"):
        clean_url = settings.PUBLIC_BASE_URL.replace("https://", "").replace("http://", "")
        stream_url = f"wss://{clean_url}/ws/twilio"
    else:
        stream_url = f"{protocol}://{host}/ws/twilio"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi">Connecting you to Placeholder Realty's qualification assistant, Riya.</Say>
    <Connect>
        <Stream url="{stream_url}">
            <Parameter name="caller" value="inbound" />
        </Stream>
    </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/api/twilio/status-callback")
async def twilio_status_callback(request: Request):
    """Callback for Twilio call status transitions."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    duration = form_data.get("CallDuration")
    logger.info(f"Twilio Call {call_sid} status: {call_status}, duration: {duration}s")
    return {"status": "received"}


# --- TWILIO MEDIA STREAM WEBSOCKET ---

@router.websocket("/ws/twilio")
async def twilio_websocket_endpoint(websocket: WebSocket):
    """
    Bidirectional WebSocket handling Twilio Media Streams audio packets.
    Decodes μ-law 8kHz audio, interacts with agent, and transmits TTS back.
    """
    await websocket.accept()
    stream_sid: Optional[str] = None
    call_sid: Optional[str] = None
    start_time = time.time()

    agent = AgentSession(
        session_id=f"twilio-{int(time.time())}",
        caller_phone="+15551234567",
        caller_name="Inbound Caller",
    )
    initial_greeting = await agent.get_initial_greeting()

    try:
        # Attempt to synthesize initial greeting
        greeting_audio = await synthesize_speech_elevenlabs(initial_greeting)

        while True:
            raw_msg = await websocket.receive_text()
            data = json.loads(raw_msg)
            event_type = data.get("event")

            if event_type == "start":
                stream_sid = data.get("streamSid")
                call_sid = data.get("start", {}).get("callSid")
                logger.info(f"Twilio Media Stream started: streamSid={stream_sid}, callSid={call_sid}")

                # Send initial greeting audio if available
                if greeting_audio and stream_sid:
                    payload_b64 = base64.b64encode(greeting_audio).decode("utf-8")
                    media_msg = {
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {"payload": payload_b64},
                    }
                    await websocket.send_text(json.dumps(media_msg))

            elif event_type == "media":
                # Raw audio payload (base64 encoded 8kHz μ-law)
                payload_raw = data.get("media", {}).get("payload")
                # Pipeline STT handles processing this stream

            elif event_type == "stop":
                logger.info(f"Twilio Media Stream stopped for streamSid={stream_sid}")
                break

    except WebSocketDisconnect:
        logger.info("Twilio WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"Error in Twilio WebSocket handler: {e}")
    finally:
        # Persist conversation
        duration = int(time.time() - start_time)
        transcript = agent.get_transcript()
        async with AsyncSessionLocal() as db:
            summary_info = await generate_llm_summary(transcript)
            outcome = ConversationOutcome.QUALIFIED.value if agent.captured_lead else ConversationOutcome.INCOMPLETE.value
            if agent.escalated:
                outcome = ConversationOutcome.ESCALATED.value

            lead_id = agent.captured_lead.id if agent.captured_lead else None
            await create_conversation(
                db=db,
                transcript=transcript,
                lead_id=lead_id,
                summary=summary_info.get("summary"),
                outcome=summary_info.get("outcome", outcome),
                duration_seconds=max(duration, 10),
            )
            await db.commit()


# --- LOCAL BROWSER WEBSOCKET AUDIO / WEBRTC ENDPOINT ---

@router.websocket("/ws/browser-audio")
async def browser_audio_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for local browser microphone testing.
    Supports audio streaming, turn-by-turn speech events, tool execution,
    TTS audio streaming, interruption handling, and live transcript streaming.
    """
    await websocket.accept()
    session_id = f"browser-{int(time.time())}"
    agent = AgentSession(session_id=session_id, caller_name="Browser User", caller_phone="+15559876543")
    start_time = time.time()

    # Send initial greeting event
    greeting = await agent.get_initial_greeting()
    greeting_audio = await synthesize_speech_elevenlabs(greeting)
    audio_b64 = base64.b64encode(greeting_audio).decode("utf-8") if greeting_audio else None

    await websocket.send_text(
        json.dumps({
            "type": "agent_speech",
            "text": greeting,
            "audio": audio_b64,
            "session_id": session_id,
        })
    )

    try:
        while True:
            raw_text = await websocket.receive_text()
            data = json.loads(raw_text)
            msg_type = data.get("type")

            # 1. Direct text/speech turn from browser
            if msg_type == "user_speech":
                user_text = data.get("text", "").strip()
                if not user_text:
                    continue

                async with AsyncSessionLocal() as db:
                    result = await agent.process_user_turn(user_text, db)
                    await db.commit()

                reply_text = result["reply"]
                audio_bytes = await synthesize_speech_elevenlabs(reply_text)
                reply_audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

                # Send response back to browser
                await websocket.send_text(
                    json.dumps({
                        "type": "agent_speech",
                        "text": reply_text,
                        "audio": reply_audio_b64,
                        "tools_called": result["tools_called"],
                        "lead_saved": result.get("lead_saved"),
                        "call_ended": result["call_ended"],
                        "escalated": result["escalated"],
                    })
                )

                if result["call_ended"]:
                    break

            # 2. Raw binary/base64 audio chunk from browser mic
            elif msg_type == "audio_chunk":
                chunk_b64 = data.get("audio")
                if chunk_b64:
                    raw_audio = base64.b64decode(chunk_b64)
                    transcription = await transcribe_audio_deepgram(raw_audio)
                    if transcription:
                        async with AsyncSessionLocal() as db:
                            result = await agent.process_user_turn(transcription, db)
                            await db.commit()

                        reply_text = result["reply"]
                        audio_bytes = await synthesize_speech_elevenlabs(reply_text)
                        reply_audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

                        await websocket.send_text(
                            json.dumps({
                                "type": "agent_speech",
                                "transcription": transcription,
                                "text": reply_text,
                                "audio": reply_audio_b64,
                                "tools_called": result["tools_called"],
                                "lead_saved": result.get("lead_saved"),
                                "call_ended": result["call_ended"],
                                "escalated": result["escalated"],
                            })
                        )

            # 3. Barge-in / User Interruption event
            elif msg_type == "interruption":
                logger.info(f"User interrupted agent speech in session {session_id}")
                # Acknowledge barge-in to stop playback on client side
                await websocket.send_text(json.dumps({"type": "interrupt_ack"}))

            # 4. User ends call
            elif msg_type == "end_call":
                logger.info(f"User requested call termination for session {session_id}")
                break

    except WebSocketDisconnect:
        logger.info(f"Browser WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Error in browser audio WebSocket: {e}", exc_info=True)
    finally:
        # Wrap up & post-call persistence
        duration = int(time.time() - start_time)
        transcript = agent.get_transcript()
        async with AsyncSessionLocal() as db:
            summary_info = await generate_llm_summary(transcript)
            outcome = ConversationOutcome.QUALIFIED.value if agent.captured_lead else ConversationOutcome.INCOMPLETE.value
            if agent.escalated:
                outcome = ConversationOutcome.ESCALATED.value

            lead_id = agent.captured_lead.id if agent.captured_lead else None
            conv = await create_conversation(
                db=db,
                transcript=transcript,
                lead_id=lead_id,
                summary=summary_info.get("summary"),
                outcome=summary_info.get("outcome", outcome),
                duration_seconds=max(duration, 5),
            )
            await db.commit()

            try:
                await websocket.send_text(
                    json.dumps({
                        "type": "call_summary",
                        "conversation_id": conv.id,
                        "summary": conv.summary,
                        "outcome": conv.outcome,
                        "duration_seconds": conv.duration_seconds,
                        "lead_id": lead_id,
                    })
                )
            except Exception:
                pass
