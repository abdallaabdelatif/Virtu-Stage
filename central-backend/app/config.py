from dotenv import load_dotenv
import os

load_dotenv()

CRUD_BASE_URL = os.getenv("CRUD_BASE_URL", "http://localhost:8000")
VOICE_ANALYSIS_WS_URL = os.getenv("VOICE_ANALYSIS_WS_URL", "ws://localhost:8001")
CONVERSATIONAL_COMPONENT_WS_URL = os.getenv(
    "CONVERSATIONAL_COMPONENT_WS_URL", "ws://localhost:8002/ws"
)
MOTION_ANALYSIS_WS_URL = os.getenv(
    "MOTION_ANALYSIS_WS_URL", "ws://localhost:9001"
)
ANALYSIS_TIMEOUT_SECONDS = int(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "600"))
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-super-secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 30)))
INTERNAL_API_KEY = os.getenv(
    "INTERNAL_API_KEY", "development-internal-key-change-me"
)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
PASSWORD_RESET_EXPIRE_MINUTES = int(
    os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "15")
)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "")
R2_SIGNED_URL_EXPIRES_SECONDS = int(
    os.getenv("R2_SIGNED_URL_EXPIRES_SECONDS", "3600")
)
GOTENBERG_URL = os.getenv("GOTENBERG_URL", "http://localhost:3001").rstrip("/")
GOTENBERG_TIMEOUT_SECONDS = int(os.getenv("GOTENBERG_TIMEOUT_SECONDS", "120"))
PRESENTATION_MAX_SLIDES = int(os.getenv("PRESENTATION_MAX_SLIDES", "100"))
PRESENTATION_IMAGE_WIDTH = int(os.getenv("PRESENTATION_IMAGE_WIDTH", "1920"))


if ENVIRONMENT == "production":
    if SECRET_KEY == "change-me-super-secret" or len(SECRET_KEY) < 32:
        raise RuntimeError("SECRET_KEY must be a unique secret of at least 32 characters")
    if INTERNAL_API_KEY == "development-internal-key-change-me" or len(INTERNAL_API_KEY) < 32:
        raise RuntimeError("INTERNAL_API_KEY must be a unique secret of at least 32 characters")
