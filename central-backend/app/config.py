from dotenv import load_dotenv
import os

load_dotenv()

CRUD_BASE_URL = os.getenv("CRUD_BASE_URL", "http://localhost:8000")
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
