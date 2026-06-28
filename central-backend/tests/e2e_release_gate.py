from __future__ import annotations

import asyncio
import json
import uuid

import httpx


CENTRAL_URL = "http://127.0.0.1:9000"


def registration_payload(username: str, email: str) -> dict[str, str]:
    return {
        "username": username,
        "email": email,
        "password": "Release@123",
        "first_name": "Release",
        "last_name": "Gate",
        "gender": "male",
    }


async def expect(
    response: httpx.Response, expected_status: int, label: str
) -> dict | list | None:
    if response.status_code != expected_status:
        raise AssertionError(
            f"{label}: expected {expected_status}, got {response.status_code}: "
            f"{response.text}"
        )
    if response.status_code == 204:
        return None
    return response.json()


async def main() -> None:
    suffix = uuid.uuid4().hex[:10]
    username = f"release.{suffix}"
    email = f"release.{suffix}@example.com"
    token: str | None = None

    async with httpx.AsyncClient(base_url=CENTRAL_URL, timeout=20.0) as client:
        invalid = await client.post(
            "/api/auth/register",
            json=registration_payload("bad username", f"invalid.{suffix}@example.com"),
        )
        await expect(invalid, 422, "invalid username validation")

        first, second = await asyncio.gather(
            client.post(
                "/api/auth/register",
                json=registration_payload(username, email.upper()),
            ),
            client.post(
                "/api/auth/register",
                json=registration_payload(username.upper(), email),
            ),
        )
        statuses = sorted([first.status_code, second.status_code])
        if statuses != [201, 409]:
            raise AssertionError(
                f"concurrent duplicate registration: expected [201, 409], got {statuses}: "
                f"{first.text} | {second.text}"
            )

        registered = first if first.status_code == 201 else second
        registration = registered.json()
        token = registration["access_token"]
        user = registration["user"]
        if user["email"] != email:
            raise AssertionError(f"email was not normalized: {user['email']}")

        auth_headers = {"Authorization": f"Bearer {token}"}

        try:
            initial_dashboard = await expect(
                await client.get("/api/dashboard/me", headers=auth_headers),
                200,
                "initial dashboard",
            )
            assert isinstance(initial_dashboard, dict)
            if initial_dashboard["total_sessions"] != 0:
                raise AssertionError("new user dashboard was not empty")

            session_id = str(uuid.uuid4())
            await expect(
                await client.post(
                    "/sessions",
                    json={
                        "session_id": session_id,
                        "user_id": user["user_id"],
                        "mode": 1,
                        "job": "Software Engineer",
                    },
                    headers=auth_headers,
                ),
                201,
                "VR session creation",
            )

            sessions = await expect(
                await client.get("/api/sessions/me", headers=auth_headers),
                200,
                "session list after creation",
            )
            assert isinstance(sessions, list)
            created_session = next(
                item for item in sessions if item["session_id"] == session_id
            )
            if created_session["status"] != "in_progress":
                raise AssertionError("created session was not in_progress")

            finished = await expect(
                await client.post(
                    f"/sessions/{session_id}/finish", headers=auth_headers
                ),
                200,
                "VR session finish",
            )
            assert isinstance(finished, dict)
            if finished["status"] != "processing" or not finished["end_time"]:
                raise AssertionError("finished session was not processing with end_time")

            await expect(
                await client.post(
                    "/voice-analyses",
                    json={
                        "session_id": session_id,
                        "anxiety_level": 20.0,
                        "confidence_level": 82.0,
                        "clarity_level": 79.0,
                        "focus_level": 85.0,
                        "pause_ratio": 0.12,
                        "pause_count": 8,
                        "longest_pause_sec": 2.4,
                        "filler_word_count": 5,
                        "words_per_minute": 137.0,
                    },
                ),
                201,
                "voice ingestion",
            )

            voice_first_report = await expect(
                await client.get(
                    f"/api/sessions/{session_id}/report", headers=auth_headers
                ),
                200,
                "voice-first report",
            )
            assert isinstance(voice_first_report, dict)
            if (
                voice_first_report["voice_status"] != "ready"
                or voice_first_report["motion_status"] != "pending"
            ):
                raise AssertionError("voice-first partial report was incorrect")

            assessment = {
                "overall_presentation": "good",
                "overall_meaning": "Solid presentation with minor issues.",
                "posture": "excellent",
                "posture_meaning": "Upright and balanced.",
                "gaze": "good",
                "gaze_meaning": "Mostly forward-facing with brief glances downward.",
                "gestures": "good",
                "gestures_meaning": "Purposeful hand movement.",
                "composure": "developing",
                "composure_meaning": "Some fidgeting was detected.",
                "stability": "excellent",
                "stability_meaning": "Head movement remained controlled.",
                "dimension_summary": {
                    "posture": "excellent",
                    "gaze": "good",
                    "gestures": "good",
                    "composure": "developing",
                    "stability": "excellent",
                },
            }
            await expect(
                await client.post(
                    "/motion-analyses",
                    json={
                        "session_id": session_id,
                        "head_stability_score": 0.82,
                        "head_movement_variance": 0.1,
                        "head_angle": 5.0,
                        "head_avg_velocity": 0.2,
                        "fidgeting_level": "low",
                        "fidgeting_score": 0.12,
                        "hand_movement_score": 74.0,
                        "left_hand_avg_velocity": 0.1,
                        "right_hand_avg_velocity": 0.1,
                        "posture_quality": 80.0,
                        "posture_score": 80.0,
                        "nervousness_indicator": 18.0,
                        "motion_overall_score": 76.0,
                        "presentation_assessment": assessment,
                        "recommendations": [
                            "Keep your gaze forward during key points.",
                            "Reduce repeated hand movement.",
                        ],
                    },
                ),
                201,
                "motion ingestion",
            )

            completed_report = await expect(
                await client.get(
                    f"/api/sessions/{session_id}/report", headers=auth_headers
                ),
                200,
                "completed report",
            )
            assert isinstance(completed_report, dict)
            if completed_report["report_status"] != "complete":
                raise AssertionError("report did not complete")
            if completed_report["session"]["status"] != "completed":
                raise AssertionError("session did not reach completed")
            if completed_report["motion_analysis"]["presentation_assessment"] != assessment:
                raise AssertionError("flat motion assessment changed in transit")

            dashboard = await expect(
                await client.get("/api/dashboard/me", headers=auth_headers),
                200,
                "completed dashboard",
            )
            assert isinstance(dashboard, dict)
            if dashboard["total_sessions"] != 1 or dashboard["analyzed_sessions"] != 1:
                raise AssertionError("completed session was not reflected in dashboard")
            if dashboard["average_overall_score"] != 78.75:
                raise AssertionError("dashboard score did not match completed report")

            final_sessions = await expect(
                await client.get("/api/sessions/me", headers=auth_headers),
                200,
                "final session list",
            )
            assert isinstance(final_sessions, list)
            final_session = next(
                item for item in final_sessions if item["session_id"] == session_id
            )
            if final_session["status"] != "completed":
                raise AssertionError("session list did not show completed status")

            print(
                json.dumps(
                    {
                        "result": "passed",
                        "registration_race": statuses,
                        "session_status": final_session["status"],
                        "report_status": completed_report["report_status"],
                        "overall_score": completed_report["session"]["overall_score"],
                        "dashboard_total_sessions": dashboard["total_sessions"],
                    },
                    indent=2,
                )
            )
        finally:
            if token:
                cleanup = await client.delete("/api/users/me", headers=auth_headers)
                await expect(cleanup, 204, "test-account cleanup")


if __name__ == "__main__":
    asyncio.run(main())
