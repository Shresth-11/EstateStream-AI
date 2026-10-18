"""
Point the test suite at a throwaway SQLite file *before* backend.config is imported,
so `pytest` never writes test leads into the developer's real_estate.db.
Also forces the offline MockLLMClient so tests stay deterministic even if .env has an OpenAI key.
"""
import os
import tempfile

_tmp_db = os.path.join(tempfile.mkdtemp(prefix="estatestream-tests-"), "test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp_db}"
os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{_tmp_db}"
os.environ["OPENAI_API_KEY"] = ""
os.environ["ELEVENLABS_API_KEY"] = ""
os.environ["CARTESIA_API_KEY"] = ""
os.environ["PHONE_PRELOAD_MODELS"] = "false"
