"""
One live phone call over the Twilio Media Streams protocol.

Inbound (caller -> us):  connected, start, media (base64 8 kHz mu-law), mark (echo), stop
Outbound (us -> caller): media (Riya's audio), mark (tells us when playback reached a point),
                         clear (flush Twilio's playback buffer = barge-in)

Turn cycle:
  caller audio -> 20 ms frames -> EnergyVAD -> utterance -> STT -> AgentSession (LLM + tools)
  -> TTS (8 kHz mu-law) -> media frames + mark -> Twilio plays it -> mark echoed -> listening

The same code serves real Twilio calls and the browser phone simulator (/phone-sim), which
speaks the identical protocol. When the simulator sends customParameters.debug = "1", we also
emit `x-debug` events (transcripts, latency) that real Twilio never receives.
"""
import asyncio
import base64
import json
import logging
import time
from typing import Any, Dict, Optional

import numpy as np
from fastapi import WebSocket

from backend.config import settings
from backend.database import AsyncSessionLocal
from voice.agent import AgentSession
from voice.telephony.codec import FRAME_SAMPLES, PHONE_RATE, ulaw_to_pcm16
from voice.telephony.engines import BaseSTT, BaseTTS, normalize_transcript
from voice.telephony.vad import EnergyVAD

logger = logging.getLogger(__name__)

SEND_CHUNK_BYTES = 640  # 80 ms of mu-law per outbound media message


class PhoneCallSession:
    def __init__(self, websocket: WebSocket, stt: Optional[BaseSTT], tts: Optional[BaseTTS]):
        self.ws = websocket
        self.stt = stt
        self.tts = tts
        self.agent = AgentSession(session_id=f"phone-{int(time.time() * 1000)}")
        self.vad = EnergyVAD()

        self.stream_sid: Optional[str] = None
        self.call_sid: Optional[str] = None
        self.debug = False
        self.started_at = time.time()

        self._send_lock = asyncio.Lock()
        self._turns: "asyncio.Queue[tuple]" = asyncio.Queue()
        self._frame_buf = np.zeros(0, dtype=np.int16)
        self._pending_marks: set = set()
        self._mark_seq = 0
        self.agent_speaking = False
        self._processing = False
        self._last_activity = time.time()
        self._hangup_requested = False
        self._closed = False
        self._tasks: list = []

    # ------------------------------------------------------------------ io
    async def _send(self, msg: Dict[str, Any]) -> None:
        if self._closed:
            return
        async with self._send_lock:
            try:
                await self.ws.send_text(json.dumps(msg))
            except Exception:
                self._closed = True

    async def _debug(self, kind: str, **data) -> None:
        if self.debug:
            await self._send({"event": "x-debug", "type": kind, **data})

    async def _send_audio(self, ulaw: bytes) -> str:
        """Queues Riya's audio on the call and returns the mark name that fires when it finishes."""
        for i in range(0, len(ulaw), SEND_CHUNK_BYTES):
            await self._send({
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {"payload": base64.b64encode(ulaw[i:i + SEND_CHUNK_BYTES]).decode()},
            })
        self._mark_seq += 1
        name = f"utt-{self._mark_seq}"
        self._pending_marks.add(name)
        self.agent_speaking = True
        await self._send({"event": "mark", "streamSid": self.stream_sid, "mark": {"name": name}})
        return name

    async def _interrupt(self) -> None:
        """Barge-in: drop everything Riya still had queued on the line."""
        if not self.agent_speaking:
            return
        logger.info(f"[{self.call_sid}] barge-in: clearing playback")
        await self._send({"event": "clear", "streamSid": self.stream_sid})
        self._pending_marks.clear()
        self.agent_speaking = False
        await self._debug("status", text="interrupted")

    # ------------------------------------------------------------- speaking
    async def speak(self, text: str) -> None:
        if not text:
            return
        if self.tts is None:
            logger.error("No TTS engine configured; caller cannot hear Riya.")
            await self._debug("error", text="No TTS engine configured")
            return
        t0 = time.perf_counter()
        try:
            audio = await self.tts.synthesize_ulaw(text)
        except Exception as e:
            logger.error(f"TTS failed: {e}", exc_info=True)
            await self._debug("error", text=f"TTS failed: {e}")
            return
        tts_ms = (time.perf_counter() - t0) * 1000
        await self._send_audio(audio)
        await self._debug("agent", text=text, tts_ms=round(tts_ms), audio_ms=round(len(audio) / PHONE_RATE * 1000))

    # --------------------------------------------------------------- turns
    async def _turn_worker(self) -> None:
        while not self._closed:
            kind, payload = await self._turns.get()
            self._processing = True
            try:
                if kind == "greeting":
                    await self.speak(payload)
                elif kind in ("audio", "silence"):
                    await self._handle_user_turn(kind, payload)
            except Exception as e:
                logger.error(f"Turn failed: {e}", exc_info=True)
                await self.speak("Sorry, something went wrong on my side. Could you repeat that?")
            finally:
                self._processing = False
                self._last_activity = time.time()

            if self.agent.call_ended and not self._hangup_requested:
                await self._request_hangup()

    async def _handle_user_turn(self, kind: str, pcm: Optional[np.ndarray]) -> None:
        t_end = time.perf_counter()
        if kind == "silence":
            text = "[silence]"
            stt_ms = 0.0
        else:
            if self.stt is None:
                await self._debug("error", text="No STT engine configured")
                return
            raw = await self.stt.transcribe(pcm)
            stt_ms = (time.perf_counter() - t_end) * 1000
            text = normalize_transcript(raw)
            if not text or len(text.strip(" .,!?")) < 2:
                await self._debug("status", text="(unintelligible, ignored)")
                return
            await self._debug("caller", text=text, raw=raw, stt_ms=round(stt_ms))

        t_llm = time.perf_counter()
        async with AsyncSessionLocal() as db:
            result = await self.agent.process_user_turn(text, db)
            await db.commit()
        llm_ms = (time.perf_counter() - t_llm) * 1000
        if result["tools_called"]:
            await self._debug("tools", tools=[
                {"name": t["name"], "arguments": t["arguments"],
                 "matches": len(t["result"]) if isinstance(t["result"], list) else None}
                for t in result["tools_called"]
            ])
        await self.speak(result["reply"])
        total_ms = (time.perf_counter() - t_end) * 1000
        logger.info(f"[{self.call_sid}] turn latency stt={stt_ms:.0f}ms agent={llm_ms:.0f}ms total={total_ms:.0f}ms")
        await self._debug("latency", stt_ms=round(stt_ms), agent_ms=round(llm_ms), total_ms=round(total_ms),
                          endpoint_ms=self.vad.cfg.end_silence_ms)

    async def _request_hangup(self) -> None:
        """Let the goodbye finish playing, then end the stream (Twilio then hangs up)."""
        self._hangup_requested = True
        await self._send({"event": "mark", "streamSid": self.stream_sid, "mark": {"name": "hangup"}})
        # Safety net in case the mark echo never arrives.
        asyncio.create_task(self._close_after(20.0))

    async def _close_after(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
        await self.close()

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await self.ws.close()
        except Exception:
            pass

    async def _silence_watchdog(self) -> None:
        timeout = settings.PHONE_SILENCE_TIMEOUT_S
        while not self._closed:
            await asyncio.sleep(0.25)
            idle = (
                self.stream_sid is not None
                and not self.agent_speaking
                and not self.vad.in_speech
                and not self._processing
                and self._turns.empty()
                and not self._hangup_requested
            )
            if idle and time.time() - self._last_activity > timeout:
                self._last_activity = time.time()
                await self._turns.put(("silence", None))

    # -------------------------------------------------------------- events
    async def _on_start(self, data: Dict[str, Any]) -> None:
        start = data.get("start", {})
        self.stream_sid = data.get("streamSid") or start.get("streamSid")
        self.call_sid = start.get("callSid")
        params = start.get("customParameters", {}) or {}
        self.debug = str(params.get("debug", "")) == "1"
        if params.get("from"):
            self.agent.caller_phone = params["from"]
        logger.info(f"Call started streamSid={self.stream_sid} callSid={self.call_sid}")
        self._tasks.append(asyncio.create_task(self._turn_worker()))
        self._tasks.append(asyncio.create_task(self._silence_watchdog()))
        await self._debug("status", text=f"connected (STT={getattr(self.stt, 'name', None)}, "
                                         f"TTS={getattr(self.tts, 'name', None)})")
        greeting = await self.agent.get_initial_greeting()
        await self._turns.put(("greeting", greeting))

    async def _on_media(self, data: Dict[str, Any]) -> None:
        if data.get("media", {}).get("track", "inbound") != "inbound":
            return
        pcm = ulaw_to_pcm16(base64.b64decode(data["media"]["payload"]))
        self._frame_buf = np.concatenate([self._frame_buf, pcm])
        while len(self._frame_buf) >= FRAME_SAMPLES:
            frame, self._frame_buf = self._frame_buf[:FRAME_SAMPLES], self._frame_buf[FRAME_SAMPLES:]
            for ev in self.vad.process(frame):
                if ev.kind == "speech_start":
                    self._last_activity = time.time()
                    await self._debug("vad", state="speech")
                elif ev.kind == "speech_end":
                    self._last_activity = time.time()
                    await self._debug("vad", state="silence")
                    if ev.audio is not None and not self._hangup_requested:
                        await self._turns.put(("audio", ev.audio))
            if (self.vad.in_speech and self.agent_speaking
                    and self.vad.speech_ms >= settings.PHONE_BARGE_IN_MS):
                await self._interrupt()

    async def _on_mark(self, data: Dict[str, Any]) -> None:
        name = data.get("mark", {}).get("name")
        if name == "hangup":
            await self.close()
            return
        self._pending_marks.discard(name)
        if not self._pending_marks and self.agent_speaking:
            self.agent_speaking = False
            self._last_activity = time.time()

    async def run(self) -> None:
        try:
            while not self._closed:
                raw = await self.ws.receive_text()
                data = json.loads(raw)
                event = data.get("event")
                if event == "start":
                    await self._on_start(data)
                elif event == "media":
                    await self._on_media(data)
                elif event == "mark":
                    await self._on_mark(data)
                elif event == "stop":
                    logger.info(f"Call stopped streamSid={self.stream_sid}")
                    break
        finally:
            self._closed = True
            for t in self._tasks:
                t.cancel()
