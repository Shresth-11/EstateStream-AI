import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Comma-separated or list of allowed CORS origins
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./real_estate.db"
    DATABASE_URL_SYNC: str = "sqlite:///./real_estate.db"

    # OpenAI / LLM
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # Deepgram STT
    DEEPGRAM_API_KEY: str = ""
    DEEPGRAM_MODEL: str = "nova-2"
    DEEPGRAM_LANGUAGE: str = "en-US"

    # ElevenLabs TTS
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    ELEVENLABS_MODEL: str = "eleven_turbo_v2_5"

    # Cartesia TTS Fallback
    CARTESIA_API_KEY: str = ""
    CARTESIA_VOICE_ID: str = "a0e998e3-18a7-4fc6-baa7-0e6205ca8337"

    # Twilio Telephony
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
