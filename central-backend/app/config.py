from dotenv import load_dotenv
import os

load_dotenv()

CRUD_BASE_URL = os.getenv("CRUD_BASE_URL", "http://localhost:8000")
VOICE_ANALYSIS_WS_URL = os.getenv("VOICE_ANALYSIS_WS_URL", "ws://localhost:8001")
CONVERSATIONAL_COMPONENT_WS_URL = os.getenv("CONVERSATIONAL_COMPONENT_WS_URL", "ws://localhost:9000/ws")
VIDEO_ANALYSIS_WS_URL = os.getenv("VIDEO_ANALYSIS_WS_URL", "ws://localhost:9001")
CENTRALIZED_BACKEND_URL = os.getenv("CENTRALIZED_BACKEND_URL", "http://localhost:9000")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-super-secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 30)))
