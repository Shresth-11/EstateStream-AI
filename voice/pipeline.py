"""
Pipecat voice pipeline orchestration for Real Estate Lead Qualification.
Connects Deepgram STT (Nova-2), LLM (GPT-4o with function calling),
and ElevenLabs TTS (Turbo v2.5) with interruption handling.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional
from fastapi import WebSocket

from backend.config import settings
from voice.prompts import RIYA_SYSTEM_PROMPT, AGENT_TOOLS_SPEC
from backend.services.property_service import search_properties
from backend.services.lead_service import save_lead
from backend.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def build_pipecat_twilio_pipeline(
    websocket: WebSocket,
    stream_sid: str,
    call_sid: str,
    on_transcript_turn: Optional[Callable[[str, str], None]] = None,
):
    """
    Constructs and runs a Pipecat pipeline bound to a Twilio Media Stream WebSocket.
    Uses TwilioFrameSerializer to serialize/deserialize 8kHz audio frames.
    """
    try:
        from pipecat.serializers.twilio import TwilioFrameSerializer
        from pipecat.transports.network.fastapi_websocket import (
            FastAPIWebsocketTransport,
            FastAPIWebsocketParams,
        )
        from pipecat.services.deepgram.stt import DeepgramSTTService
        from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
        from pipecat.services.openai.llm import OpenAILLMService
        from pipecat.pipeline.pipeline import Pipeline
        from pipecat.pipeline.runner import PipelineRunner
        from pipecat.pipeline.task import PipelineTask, PipelineParams
        from pipecat.processors.aggregators.llm_response import (
            LLMUserResponseAggregator,
            LLMAssistantResponseAggregator,
        )

        serializer = TwilioFrameSerializer(
            stream_sid=stream_sid,
            call_sid=call_sid,
            account_sid=settings.TWILIO_ACCOUNT_SID or None,
            auth_token=settings.TWILIO_AUTH_TOKEN or None,
        )

        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_out_enabled=True,
                add_wav_header=False,
                serializer=serializer,
            ),
        )

        stt = DeepgramSTTService(
            api_key=settings.DEEPGRAM_API_KEY,
            model=settings.DEEPGRAM_MODEL,
            language=settings.DEEPGRAM_LANGUAGE,
        )

        tts = ElevenLabsTTSService(
            api_key=settings.ELEVENLABS_API_KEY,
            voice_id=settings.ELEVENLABS_VOICE_ID,
            model=settings.ELEVENLABS_MODEL,
        )

        llm = OpenAILLMService(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
        )

        pipeline = Pipeline([
            transport.input(),
            stt,
            llm,
            tts,
            transport.output(),
        ])

        task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))
        runner = PipelineRunner()
        await runner.run(task)

    except Exception as e:
        logger.error(f"Pipecat pipeline initialization error: {e}", exc_info=True)
        raise
