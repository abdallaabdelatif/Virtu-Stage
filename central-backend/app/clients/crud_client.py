from __future__ import annotations

from typing import Any

import httpx

from app.config import CRUD_BASE_URL, INTERNAL_API_KEY


class CRUDClient:
    def __init__(self) -> None:
        self.base = CRUD_BASE_URL.rstrip("/")
        self.internal_headers = {"X-Internal-API-Key": INTERNAL_API_KEY}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        internal: bool = False,
        timeout: float = 10.0,
    ) -> httpx.Response:
        headers = self.internal_headers if internal else None
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base}{path}",
                json=json,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            return response

    async def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._request("POST", "/users", json=payload)
        response.raise_for_status()
        return response.json()

    async def login_verify(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._request(
            "POST", "/internal/auth/login", json=payload, internal=True
        )
        response.raise_for_status()
        return response.json()

    async def create_voice_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._request(
            "POST", "/voice-analysis", json=payload, internal=True
        )
        response.raise_for_status()
        return response.json()

    async def create_motion_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._request(
            "POST", "/motion-analysis", json=payload, internal=True, timeout=30.0
        )
        response.raise_for_status()
        return response.json()

    async def create_training_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._request(
            "POST", "/sessions", json=payload, internal=True
        )
        response.raise_for_status()
        return response.json()

    async def finish_training_session(self, session_id: str) -> dict[str, Any]:
        response = await self._request(
            "POST", f"/sessions/{session_id}/finish", internal=True
        )
        response.raise_for_status()
        return response.json()

    async def get_training_session(self, session_id: str) -> dict[str, Any] | None:
        response = await self._request(
            "GET", f"/sessions/{session_id}", internal=True
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def list_training_sessions_by_user(
        self, user_id: str
    ) -> list[dict[str, Any]]:
        response = await self._request(
            "GET", f"/sessions/user/{user_id}", internal=True
        )
        response.raise_for_status()
        return response.json()

    async def get_voice_analysis_by_session(
        self, session_id: str
    ) -> dict[str, Any] | None:
        response = await self._request(
            "GET", f"/voice-analysis/session/{session_id}", internal=True
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def get_motion_analysis_by_session(
        self, session_id: str
    ) -> dict[str, Any] | None:
        response = await self._request(
            "GET", f"/motion-analysis/session/{session_id}", internal=True
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        response = await self._request("GET", f"/users/{user_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        response = await self._request(
            "POST",
            "/internal/users/by-email",
            json={"email": email},
            internal=True,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def store_password_reset_token(self, payload: dict[str, Any]) -> None:
        response = await self._request(
            "POST",
            "/internal/password-reset/request",
            json=payload,
            internal=True,
        )
        response.raise_for_status()

    async def reset_password(
        self, token_hash: str, new_password: str
    ) -> dict[str, Any]:
        response = await self._request(
            "POST",
            "/internal/password-reset/reset",
            json={"token_hash": token_hash, "new_password": new_password},
            internal=True,
        )
        response.raise_for_status()
        return response.json()

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> dict[str, Any]:
        response = await self._request(
            "PATCH",
            "/internal/auth/change-password",
            json={
                "user_id": user_id,
                "current_password": current_password,
                "new_password": new_password,
            },
            internal=True,
        )
        response.raise_for_status()
        return response.json()

    async def update_user_status(self, user_id: str, is_active: bool) -> dict[str, Any]:
        response = await self._request(
            "PATCH",
            f"/internal/users/{user_id}/status",
            json={"is_active": is_active},
            internal=True,
        )
        response.raise_for_status()
        return response.json()

    async def update_user_profile(
        self,
        user_id: str,
        first_name: str,
        last_name: str,
    ) -> dict[str, Any]:
        response = await self._request(
            "PATCH",
            f"/internal/users/{user_id}/profile",
            json={"first_name": first_name, "last_name": last_name},
            internal=True,
        )
        response.raise_for_status()
        return response.json()

    async def delete_user(self, user_id: str) -> None:
        response = await self._request(
            "DELETE", f"/users/{user_id}", internal=True
        )
        response.raise_for_status()

    async def get_user_dashboard(self, user_id: str) -> dict[str, Any]:
        response = await self._request(
            "GET", f"/aggregates/users/{user_id}/dashboard", internal=True
        )
        response.raise_for_status()
        return response.json()

    async def get_admin_dashboard(self) -> dict[str, Any]:
        response = await self._request(
            "GET", "/aggregates/admin/dashboard", internal=True
        )
        response.raise_for_status()
        return response.json()

    async def list_admin_users(self) -> list[dict[str, Any]]:
        response = await self._request(
            "GET", "/aggregates/admin/users", internal=True
        )
        response.raise_for_status()
        return response.json()

    async def create_library_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._request(
            "POST", "/files", json=payload, internal=True, timeout=30.0
        )
        response.raise_for_status()
        return response.json()

    async def list_library_files(self, user_id: str) -> list[dict[str, Any]]:
        response = await self._request(
            "GET", f"/files/user/{user_id}", internal=True
        )
        response.raise_for_status()
        return response.json()

    async def get_library_file(self, file_id: str) -> dict[str, Any] | None:
        response = await self._request("GET", f"/files/{file_id}", internal=True)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def delete_library_file(self, file_id: str) -> None:
        response = await self._request("DELETE", f"/files/{file_id}", internal=True)
        response.raise_for_status()

    async def update_library_file_processing(
        self, file_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        response = await self._request(
            "PATCH",
            f"/files/{file_id}/processing",
            json=payload,
            internal=True,
        )
        response.raise_for_status()
        return response.json()

    async def get_presentation_slides(self, file_id: str) -> list[dict[str, Any]]:
        response = await self._request(
            "GET", f"/files/{file_id}/slides", internal=True
        )
        response.raise_for_status()
        return response.json()

    async def replace_presentation_slides(
        self, file_id: str, slides: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        response = await self._request(
            "PUT",
            f"/files/{file_id}/slides",
            json={"slides": slides},
            internal=True,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


crud_client = CRUDClient()
