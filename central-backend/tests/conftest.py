import sys
from pathlib import Path

import pytest

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app
from app.testing_allure import allure


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


_ALLURE_FEATURES = {
    "test_api_auth.py": ("Authentication", "Registration and login validation"),
    "test_api_account.py": ("Account Management", "Protected routes and user account settings"),
    "test_api_vr.py": ("VR Session API", "VR sessions, voice ingestion, and motion ingestion"),
    "test_api_sessions.py": ("Session Reports", "Session listing, ownership, status, and reports"),
    "test_api_files.py": ("Presentation Files", "Upload, processing, storage, and slide retrieval"),
    "test_api_dashboard.py": ("Dashboard and Admin", "User analytics and administrator APIs"),
    "test_api_avatars.py": ("Avatars", "Avatar upload, normalization, and public reads"),
    "test_clients.py": ("Service Proxies", "Voice and conversational WebSocket proxy clients"),
}


@pytest.fixture(autouse=True)
def label_allure_report(request):
    feature, story = _ALLURE_FEATURES.get(
        request.node.path.name,
        ("Backend API", "General backend behavior"),
    )
    allure.dynamic.epic("VirtuStage Backend Testing")
    allure.dynamic.feature(feature)
    allure.dynamic.story(story)
    allure.dynamic.suite(request.node.path.stem)
    allure.dynamic.title(request.node.name.replace("_", " "))

    name = request.node.name.lower()
    if any(token in name for token in ("requires", "rejects", "duplicate", "invalid", "forbidden", "cannot")):
        allure.dynamic.severity(allure.severity_level.CRITICAL)
    else:
        allure.dynamic.severity(allure.severity_level.NORMAL)
