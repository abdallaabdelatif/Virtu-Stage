import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
    VOICE_ANALYSIS_WS_URL = os.getenv("VOICE_ANALYSIS_WS_URL", "ws://localhost:8001")
    VOICE_ANALYSIS_SESSION_ID = os.getenv("VOICE_ANALYSIS_SESSION_ID", "")


settings = Settings()