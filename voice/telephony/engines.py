"""
Pluggable speech engines for the phone pipeline.

STT (speech -> text), chosen by settings.STT_ENGINE ("auto" | "deepgram" | "whisper"):
  - deepgram: Deepgram Nova REST on each utterance (needs DEEPGRAM_API_KEY, paid w/ signup credit)
  - whisper:  faster-whisper running locally on CPU (free, offline)
TTS (text -> 8 kHz mu-law), chosen by settings.TTS_ENGINE ("auto" | "elevenlabs" | "piper"):
  - elevenlabs: requests output_format=ulaw_8000 directly, no conversion needed
  - piper:      local neural TTS (free, offline), resampled + mu-law encoded here

"auto" prefers the hosted engine when its key is set, else the local one.
Blocking model calls run in a thread so the event loop keeps streaming audio.
"""
import asyncio
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

import httpx
import numpy as np

from backend.config import settings
from voice.telephony.codec import (
    PHONE_RATE, float_to_pcm16, pcm16_to_float, pcm16_to_ulaw, resample,
)

logger = logging.getLogger(__name__)

# Vocabulary hint for Whisper: without it "BHK" comes out as "BSK"/"BHQ".
WHISPER_PROMPT = (
    "Phone call with a real estate agent about apartments. "
    "BHK, 1 BHK, 2 BHK, 3 BHK, Downtown, Midtown, Uptown, West End, Silicon Hills, budget, lakh, crore."
)

_HOMOPHONES = [
    (re.compile(r"\b(to|too|two)[\s,.-]*(bhk|bhks|b h k|bsk|bhq|vhk)\b", re.I), "2 BHK"),
    (re.compile(r"\b(for|four)[\s,.-]*(bhk|bhks|b h k|bsk|bhq|vhk)\b", re.I), "4 BHK"),
    (re.compile(r"\b(one|won)[\s,.-]*(bhk|bhks|b h k|bsk|bhq|vhk)\b", re.I), "1 BHK"),
    (re.compile(r"\b(three|tree)[\s,.-]*(bhk|bhks|b h k|bsk|bhq|vhk)\b", re.I), "3 BHK"),
    (re.compile(r"\b(\d)[\s-]*(bhks|b h k|bsk|bhq|vhk)\b", re.I), r"\1 BHK"),
]


def normalize_transcript(text: str) -> str:
    """Fixes the phone-audio misrecognitions that matter for this domain."""
    t = (text or "").strip()
    for pattern, repl in _HOMOPHONES:
        t = pattern.sub(repl, t)
    return t


# ----------------------------- STT -----------------------------

class BaseSTT:
    name = "base"

    async def transcribe(self, pcm8k: np.ndarray) -> str:
        raise NotImplementedError


class DeepgramSTT(BaseSTT):
    name = "deepgram"

    async def transcribe(self, pcm8k: np.ndarray) -> str:
        url = (
            "https://api.deepgram.com/v1/listen"
            f"?model={settings.DEEPGRAM_MODEL}&language={settings.DEEPGRAM_LANGUAGE}"
            f"&smart_format=true&encoding=linear16&sample_rate={PHONE_RATE}&channels=1"
            "&keywords=BHK:2&keywords=Midtown&keywords=Uptown"
        )
        headers = {"Authorization": f"Token {settings.DEEPGRAM_API_KEY}", "Content-Type": "audio/raw"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(url, headers=headers, content=np.asarray(pcm8k, dtype=np.int16).tobytes())
        if r.status_code != 200:
            raise RuntimeError(f"Deepgram {r.status_code}: {r.text[:200]}")
        alt = r.json()["results"]["channels"][0]["alternatives"][0]
        return alt.get("transcript", "")


class WhisperSTT(BaseSTT):
    name = "whisper"

    def __init__(self):
        from faster_whisper import WhisperModel  # optional dependency
        self.model = WhisperModel(
            settings.WHISPER_MODEL,
            device="cpu",
            compute_type="int8",
            download_root=str(Path(settings.MODELS_DIR) / "whisper"),
            cpu_threads=max(1, (os.cpu_count() or 2) - 1),
        )

    def _run(self, pcm8k: np.ndarray) -> str:
        audio16k = resample(pcm16_to_float(pcm8k), PHONE_RATE, 16000)
        segments, _ = self.model.transcribe(
            audio16k,
            language="en",
            beam_size=1,
            initial_prompt=WHISPER_PROMPT,
            condition_on_previous_text=False,
            vad_filter=False,  # our own VAD already cut the utterance
        )
        return " ".join(s.text.strip() for s in segments)

    async def transcribe(self, pcm8k: np.ndarray) -> str:
        return await asyncio.to_thread(self._run, pcm8k)


# ----------------------------- TTS -----------------------------

class BaseTTS:
    name = "base"

    async def synthesize_ulaw(self, text: str) -> bytes:
        raise NotImplementedError


class ElevenLabsPhoneTTS(BaseTTS):
    name = "elevenlabs"

    async def synthesize_ulaw(self, text: str) -> bytes:
        url = (
            f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}"
            "?output_format=ulaw_8000"
        )
        headers = {"xi-api-key": settings.ELEVENLABS_API_KEY, "Content-Type": "application/json"}
        payload = {"text": text, "model_id": settings.ELEVENLABS_MODEL,
                   "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(url, headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:200]}")
        return r.content


class PiperTTS(BaseTTS):
    name = "piper"

    def __init__(self):
        from piper import PiperVoice  # optional dependency
        model_dir = Path(settings.MODELS_DIR) / "piper"
        model_path = model_dir / f"{settings.PIPER_VOICE}.onnx"
        if not model_path.exists():
            from piper.download_voices import download_voice
            model_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Downloading Piper voice {settings.PIPER_VOICE} (one-time, ~60 MB)...")
            download_voice(settings.PIPER_VOICE, model_dir)
        self.voice = PiperVoice.load(str(model_path))

    def _run(self, text: str) -> bytes:
        chunks = list(self.voice.synthesize(text))
        if not chunks:
            return b""
        pcm = np.concatenate([np.frombuffer(c.audio_int16_bytes, dtype=np.int16) for c in chunks])
        audio8k = resample(pcm16_to_float(pcm), chunks[0].sample_rate, PHONE_RATE)
        return pcm16_to_ulaw(float_to_pcm16(audio8k))

    async def synthesize_ulaw(self, text: str) -> bytes:
        return await asyncio.to_thread(self._run, text)


# ----------------------------- selection -----------------------------

def _has_key(value: str) -> bool:
    return bool(value and value.strip() and not value.startswith("your_"))


@lru_cache(maxsize=1)
def get_stt() -> Optional[BaseSTT]:
    choice = settings.STT_ENGINE.lower()
    if choice in ("deepgram",) or (choice == "auto" and _has_key(settings.DEEPGRAM_API_KEY)):
        return DeepgramSTT()
    try:
        return WhisperSTT()
    except ImportError:
        logger.error("No STT engine: set DEEPGRAM_API_KEY or `pip install -r requirements-voice.txt`.")
    except Exception as e:
        logger.error(f"Failed to load Whisper: {e}")
    return None


@lru_cache(maxsize=1)
def get_tts() -> Optional[BaseTTS]:
    choice = settings.TTS_ENGINE.lower()
    if choice in ("elevenlabs",) or (choice == "auto" and _has_key(settings.ELEVENLABS_API_KEY)):
        return ElevenLabsPhoneTTS()
    try:
        return PiperTTS()
    except ImportError:
        logger.error("No TTS engine: set ELEVENLABS_API_KEY or `pip install -r requirements-voice.txt`.")
    except Exception as e:
        logger.error(f"Failed to load Piper: {e}")
    return None


async def warm_up() -> None:
    """Loads models before the first call so caller #1 doesn't wait ~3 s."""
    stt = await asyncio.to_thread(get_stt)
    tts = await asyncio.to_thread(get_tts)
    logger.info(f"Phone pipeline ready: STT={getattr(stt, 'name', None)} TTS={getattr(tts, 'name', None)}")
