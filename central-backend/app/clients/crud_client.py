from __future__ import annotations

from typing import Any

import httpx

from app.config import CRUD_BASE_URL, INTERNAL_API_KEY


class CRUDClient:
    def __init__(self) -> None:
        self.base = CRUD_BASE_URL.rstrip("/")
        self.internal_headers = {"X-Internal-API-Key": INTERNAL_API_KEY}

    async def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base}/users", json=payload, timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    async def login_verify(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base}/internal/auth/login",
                json=payload,
                headers=self.internal_headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def create_voice_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base}/voice-analysis", json=payload, timeout=10.0)
            r.raise_for_status()
            return r.json()

    async def create_motion_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base}/motion-analysis", json=payload, timeout=30.0)
            r.raise_for_status()
            return r.json()

    async def create_training_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base}/sessions", json=payload, timeout=10.0)
            r.raise_for_status()
            return r.json()

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base}/users/{user_id}", timeout=10.0
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def get_user_by_email(
        self, email: str
    ) -> dict[str, Any] | None:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base}/internal/users/by-email",
                json={"email": email},
                headers=self.internal_headers,
                timeout=10.0,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def store_password_reset_token(
        self, payload: dict[str, Any]
    ) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base}/internal/password-reset/request",
                json=payload,
                headers=self.internal_headers,
                timeout=10.0,
            )
            response.raise_for_status()

    async def reset_password(
        self, token_hash: str, new_password: str
    ) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base}/internal/password-reset/reset",
                json={
                    "token_hash": token_hash,
                    "new_password": new_password,
                },
                headers=self.internal_headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base}/internal/auth/change-password",
                json={
                    "user_id": user_id,
                    "current_password": current_password,
                    "new_password": new_password,
                },
                headers=self.internal_headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def update_user_status(
        self, user_id: str, is_active: bool
    ) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base}/internal/users/{user_id}/status",
                json={"is_active": is_active},
                headers=self.internal_headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def update_user_profile(
        self,
        user_id: str,
        first_name: str,
        last_name: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base}/internal/users/{user_id}/profile",
                json={
                    "first_name": first_name,
                    "last_name": last_name,
                },
                headers=self.internal_headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def delete_user(self, user_id: str) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base}/users/{user_id}",
                headers=self.internal_headers,
                timeout=10.0,
            )
            response.raise_for_status()


crud_client = CRUDClient()
