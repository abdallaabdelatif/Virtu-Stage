from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()

CENTRALIZED_BACKEND_URL = os.getenv("CENTRALIZED_BACKEND_URL", "http://localhost:9000")
VOICE_ANALYSIS_RESULT_CALLBACK_URL = os.getenv(
    "VOICE_ANALYSIS_RESULT_CALLBACK_URL",
    f"{CENTRALIZED_BACKEND_URL.rstrip('/')}/voice-analyses",
)
INTERNAL_API_KEY = os.getenv(
    "INTERNAL_API_KEY", "development-internal-key-change-me"
)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

if ENVIRONMENT == "production" and (
    INTERNAL_API_KEY == "development-internal-key-change-me"
    or len(INTERNAL_API_KEY) < 32
):
    raise RuntimeError("INTERNAL_API_KEY must be a unique secret of at least 32 characters")
