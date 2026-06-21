from dotenv import load_dotenv
import os

load_dotenv()

CRUD_BASE_URL = os.getenv("CRUD_BASE_URL", "http://localhost:8000")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-super-secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 30)))
