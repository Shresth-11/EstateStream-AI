"""
Audio Services: Deepgram STT and ElevenLabs TTS Integration with fallbacks.
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional
import httpx
from backend.config import settings

logger = logging.getLogger(__name__)


async def transcribe_audio_deepgram(audio_bytes: bytes, content_type: str = "audio/wav") -> Optional[str]:
    """
    Transcribes audio bytes using Deepgram Nova-2 REST or streaming endpoint.
    """
    if not settings.DEEPGRAM_API_KEY or settings.DEEPGRAM_API_KEY.startswith("your_"):
        logger.warning("Deepgram API key not configured.")
        return None

    try:
        url = f"https://api.deepgram.com/v1/listen?model={settings.DEEPGRAM_MODEL}&language={settings.DEEPGRAM_LANGUAGE}&smart_format=true"
        headers = {
            "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
            "Content-Type": content_type,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, content=audio_bytes)
            if response.status_code == 200:
                data = response.json()
                transcript = (
                    data.get("results", {})
                    .get("channels", [{}])[0]
                    .get("alternatives", [{}])[0]
                    .get("transcript", "")
                )
                return transcript.strip() if transcript else None
            else:
                logger.error(f"Deepgram STT error {response.status_code}: {response.text}")
                return None
    except Exception as e:
        logger.error(f"Exception during Deepgram transcription: {e}")
        return None


async def synthesize_speech_elevenlabs(text: str) -> Optional[bytes]:
    """
    Synthesizes speech audio (MP3/PCM) using ElevenLabs Turbo v2.5 model.
    Falls back to Cartesia if configured.
    """
    if not text or not text.strip():
        return None

    # Try ElevenLabs first
    if settings.ELEVENLABS_API_KEY and not settings.ELEVENLABS_API_KEY.startswith("your_"):
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}?output_format=mp3_44100_128"
            headers = {
                "xi-api-key": settings.ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            }
            payload = {
                "text": text,
                "model_id": settings.ELEVENLABS_MODEL,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    return resp.content
                else:
                    logger.warning(f"ElevenLabs TTS failed with code {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Exception in ElevenLabs TTS: {e}")

    # Fallback to Cartesia if ElevenLabs fails or is not configured
    if settings.CARTESIA_API_KEY and not settings.CARTESIA_API_KEY.startswith("your_"):
        try:
            url = "https://api.cartesia.ai/tts/bytes"
            headers = {
                "X-API-Key": settings.CARTESIA_API_KEY,
                "Cartesia-Version": "2024-06-10",
                "Content-Type": "application/json",
            }
            payload = {
                "transcript": text,
                "model_id": "sonic-english",
                "voice": {"mode": "id", "id": settings.CARTESIA_VOICE_ID},
                "output_format": {"container": "raw", "encoding": "pcm_s16le", "sample_rate": 24000},
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    return resp.content
        except Exception as e:
            logger.error(f"Exception in Cartesia fallback: {e}")

    return None
