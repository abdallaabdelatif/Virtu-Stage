from __future__ import annotations
import httpx
from typing import Any
from app.config import CRUD_BASE_URL


class CRUDClient:
    def __init__(self) -> None:
        self.base = CRUD_BASE_URL.rstrip("/")

    async def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base}/users", json=payload, timeout=10.0)
            r.raise_for_status()
            return r.json()

    async def login_verify(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Call CRUD internal auth verify endpoint to check credentials."""
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base}/internal/auth/login", json=payload, timeout=10.0)
            if r.status_code == 200:
                return r.json()
            return None

    async def create_voice_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base}/voice-analysis", json=payload, timeout=10.0)
            r.raise_for_status()
            return r.json()

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base}/users/{user_id}", timeout=10.0)
            if r.status_code == 200:
                return r.json()
            return None


crud_client = CRUDClient()
