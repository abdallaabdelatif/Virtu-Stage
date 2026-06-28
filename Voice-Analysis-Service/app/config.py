from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()

CENTRALIZED_BACKEND_URL = os.getenv("CENTRALIZED_BACKEND_URL", "http://localhost:9000")
VOICE_ANALYSIS_RESULT_CALLBACK_URL = os.getenv(
    "VOICE_ANALYSIS_RESULT_CALLBACK_URL",
    f"{CENTRALIZED_BACKEND_URL.rstrip('/')}/voice-analyses",
)
