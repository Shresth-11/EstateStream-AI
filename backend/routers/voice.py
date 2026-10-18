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
from backend.services.conversation_service import persist_session
from voice.agent import AgentSession
from voice.audio_services import synthesize_speech_elevenlabs, transcribe_audio_deepgram

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Voice Telephony & Browser Audio"])


# --- TWILIO TELEPHONY WEBHOOKS ---

@router.api_route("/api/twilio/incoming-call", methods=["GET", "POST"])
async def twilio_incoming_call(request: Request):
    """
    Twilio Voice webhook for inbound calls.
    Returns TwiML connecting the call to the WebSocket Media Stream.
    """
    caller_number = ""
    if request.method == "POST":
        try:
            form = await request.form()
            caller_number = str(form.get("From") or "")
        except Exception:
            caller_number = ""
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
    <Connect>
        <Stream url="{stream_url}">
            <Parameter name="caller" value="inbound" />
            <Parameter name="from" value="{caller_number}" />
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


# --- TWILIO MEDIA STREAM WEBSOCKET (live phone pipeline) ---

@router.websocket("/ws/twilio")
async def twilio_websocket_endpoint(websocket: WebSocket):
    """
    Live phone calls over the Twilio Media Streams protocol: server-side voice activity
    detection, speech-to-text, the agent, text-to-speech and barge-in. Also used, unchanged,
    by the free browser phone simulator at /phone-sim.
    """
    from voice.telephony.engines import get_stt, get_tts
    from voice.telephony.phone_session import PhoneCallSession

    await websocket.accept()
    stt = await asyncio.to_thread(get_stt)
    tts = await asyncio.to_thread(get_tts)
    call = PhoneCallSession(websocket, stt, tts)
    try:
        await call.run()
    except WebSocketDisconnect:
        logger.info("Twilio media stream disconnected.")
    except Exception as e:
        logger.error(f"Error in phone call handler: {e}", exc_info=True)
    finally:
        try:
            async with AsyncSessionLocal() as db:
                conv = await persist_session(db, call.agent, time.time() - call.started_at)
                await db.commit()
            logger.info(f"Phone call saved as conversation #{conv.id} ({conv.outcome})")
        except Exception as e:
            logger.error(f"Failed to persist phone call: {e}", exc_info=True)


async def _run_turn_and_reply(websocket: WebSocket, agent: AgentSession, user_text: str, extra: Optional[dict] = None) -> dict:
    """Runs one agent turn, synthesizes speech, and sends the agent_speech packet."""
    async with AsyncSessionLocal() as db:
        result = await agent.process_user_turn(user_text, db)
        await db.commit()
    reply_text = result["reply"]
    audio_bytes = await synthesize_speech_elevenlabs(reply_text)
    packet = {
        "type": "agent_speech",
        "text": reply_text,
        "audio": base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None,
        "tools_called": result["tools_called"],
        "lead_saved": result.get("lead_saved"),
        "call_ended": result["call_ended"],
        "escalated": result["escalated"],
    }
    if extra:
        packet.update(extra)
    await websocket.send_text(json.dumps(packet, default=str))
    return result


# --- LOCAL BROWSER WEBSOCKET AUDIO ENDPOINT ---

@router.websocket("/ws/browser-audio")
async def browser_audio_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for local browser microphone testing.
    Supports turn-by-turn speech events, tool execution,
    TTS audio streaming, interruption handling, and live transcript streaming.
    """
    await websocket.accept()
    session_id = f"browser-{int(time.time())}"
    agent = AgentSession(session_id=session_id)
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
                # Empty text is treated as a silence turn (the client sends one after an idle timeout).
                user_text = (data.get("text") or "").strip() or "[silence]"

                result = await _run_turn_and_reply(websocket, agent, user_text)
                if result["call_ended"]:
                    break

            # 2. Raw binary/base64 audio chunk from browser mic
            elif msg_type == "audio_chunk":
                chunk_b64 = data.get("audio")
                if chunk_b64:
                    raw_audio = base64.b64decode(chunk_b64)
                    transcription = await transcribe_audio_deepgram(raw_audio)
                    if transcription:
                        result = await _run_turn_and_reply(websocket, agent, transcription, {"transcription": transcription})
                        if result["call_ended"]:
                            break

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
        conv = None
        try:
            async with AsyncSessionLocal() as db:
                conv = await persist_session(db, agent, time.time() - start_time)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to persist browser session {session_id}: {e}", exc_info=True)
        if conv is not None:
            try:
                await websocket.send_text(
                    json.dumps({
                        "type": "call_summary",
                        "conversation_id": conv.id,
                        "summary": conv.summary,
                        "outcome": conv.outcome,
                        "duration_seconds": conv.duration_seconds,
                        "lead_id": conv.lead_id,
                    })
                )
            except Exception:
                pass
