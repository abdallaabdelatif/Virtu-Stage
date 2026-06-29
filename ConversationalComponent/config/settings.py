import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
    CENTRAL_BACKEND_WS_URL = os.getenv("CENTRAL_BACKEND_WS_URL", "ws://localhost:9000")
    INTERNAL_API_KEY = os.getenv(
        "INTERNAL_API_KEY", "development-internal-key-change-me"
    )
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

    @classmethod
    def validate_runtime(cls) -> None:
        missing = [
            name
            for name in (
                "OPENAI_API_KEY",
                "DEEPGRAM_API_KEY",
                "ELEVENLABS_API_KEY",
                "ELEVENLABS_VOICE_ID",
            )
            if not getattr(cls, name)
        ]
        if missing:
            raise RuntimeError(f"Missing required variables: {', '.join(missing)}")
        if cls.ENVIRONMENT == "production" and (
            cls.INTERNAL_API_KEY == "development-internal-key-change-me"
            or len(cls.INTERNAL_API_KEY) < 32
        ):
            raise RuntimeError(
                "INTERNAL_API_KEY must be a unique secret of at least 32 characters"
            )


settings = Settings()
