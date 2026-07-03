import uuid
from datetime import datetime, timezone

import pytest

import app.services.dashboard_aggregates as dashboard_aggregates


@pytest.mark.asyncio
async def test_user_dashboard_aggregate(client, user_id):
    session_ids = [str(uuid.uuid4()) for _ in range(11)]
    for index, session_id in enumerate(session_ids):
        await client.post(
            "/sessions",
            json={
                "session_id": session_id,
                "user_id": user_id,
                "scenario_type": "interview",
                "difficulty_level": "medium",
            },
            headers={"X-Internal-API-Key": "test-internal-key"},
        )
        await client.post(
            f"/sessions/{session_id}/finish",
            headers={"X-Internal-API-Key": "test-internal-key"},
        )
        await client.put(
            f"/sessions/{session_id}",
            json={
                "status": "completed",
                "overall_score": 70 + index,
                "voice_analysis_score": 72 + index,
                "motion_analysis_score": 68 + index,
            },
            headers={"X-Internal-API-Key": "test-internal-key"},
        )

    response = await client.get(
        f"/aggregates/users/{user_id}/dashboard",
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_sessions"] == 11
    assert body["analyzed_sessions"] == 11
    assert body["average_overall_score"] == 75.0
    assert body["improvement_rate"] == 6.85
    assert len(body["score_history"]) == 11
    assert len(body["analysis_history"]) == 10
    assert all(point["timestamp"] for point in body["score_history"])
    assert all(point["timestamp"] for point in body["analysis_history"])


@pytest.mark.asyncio
async def test_admin_dashboard_and_users_aggregate(client, user_id):
    session_id = str(uuid.uuid4())
    await client.post(
        "/sessions",
        json={
            "session_id": session_id,
            "user_id": user_id,
            "scenario_type": "interview",
            "difficulty_level": "medium",
        },
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    await client.put(
        f"/sessions/{session_id}",
        json={"status": "completed", "overall_score": 80.0},
        headers={"X-Internal-API-Key": "test-internal-key"},
    )

    dashboard_response = await client.get(
        "/aggregates/admin/dashboard",
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["total_users"] >= 1
    assert dashboard["total_sessions"] >= 1
    assert dashboard["platform_average_score"] == 80.0

    users_response = await client.get(
        "/aggregates/admin/users",
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert users_response.status_code == 200
    users = users_response.json()
    assert any(user["user_id"] == user_id for user in users)
    target = next(user for user in users if user["user_id"] == user_id)
    assert target["session_count"] == 1


@pytest.mark.asyncio
async def test_admin_dashboard_uses_cairo_day_boundaries(
    client, user_id, monkeypatch
):
    monkeypatch.setattr(
        dashboard_aggregates,
        "_utc_now",
        lambda: datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc),
    )
    start_times = [
        "2026-06-28T20:59:59+00:00",  # Jun 28, 11:59:59 PM in Cairo
        "2026-06-28T21:00:00+00:00",  # Jun 29, 12:00 AM in Cairo
        "2026-06-29T20:59:59+00:00",  # Jun 29, 11:59:59 PM in Cairo
    ]

    for start_time in start_times:
        session_id = str(uuid.uuid4())
        response = await client.post(
            "/sessions",
            json={
                "session_id": session_id,
                "user_id": user_id,
                "scenario_type": "interview",
                "difficulty_level": "medium",
            },
            headers={"X-Internal-API-Key": "test-internal-key"},
        )
        assert response.status_code == 201
        response = await client.put(
            f"/sessions/{session_id}",
            json={"start_time": start_time},
            headers={"X-Internal-API-Key": "test-internal-key"},
        )
        assert response.status_code == 200

    response = await client.get(
        "/aggregates/admin/dashboard",
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["sessions_today"] == 2
    assert {point["date"]: point["count"] for point in dashboard["sessions_by_day"]} == {
        "2026-06-28": 1,
        "2026-06-29": 2,
    }
