import uuid

import pytest


@pytest.mark.asyncio
async def test_session_lifecycle_and_scoring(client, user_id):
    session_id = str(uuid.uuid4())

    create_response = await client.post(
        "/sessions",
        json={
            "session_id": session_id,
            "user_id": user_id,
            "scenario_type": "interview",
            "difficulty_level": "medium",
        },
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "in_progress"
    assert created["start_time"] is not None

    finish_response = await client.post(
        f"/sessions/{session_id}/finish",
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert finish_response.status_code == 200
    finished = finish_response.json()
    assert finished["status"] == "processing"
    assert finished["end_time"] is not None

    voice_payload = {
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
    }
    voice_response = await client.post(
        "/voice-analysis",
        json=voice_payload,
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert voice_response.status_code == 201
    assert voice_response.json()["session_id"] == session_id

    session_after_voice = await client.get(
        f"/sessions/{session_id}",
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert session_after_voice.json()["voice_analysis_score"] == 81.5
    assert session_after_voice.json()["status"] == "processing"

    motion_payload = {
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
    }
    motion_response = await client.post(
        "/motion-analysis",
        json=motion_payload,
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert motion_response.status_code == 201

    completed = await client.get(
        f"/sessions/{session_id}",
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    completed_body = completed.json()
    assert completed_body["status"] == "completed"
    assert completed_body["overall_score"] == 78.75


@pytest.mark.asyncio
async def test_voice_analysis_ingestion_is_idempotent(client, user_id):
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

    payload = {
        "session_id": session_id,
        "anxiety_level": 20.0,
        "confidence_level": 80.0,
        "clarity_level": 75.0,
        "focus_level": 70.0,
        "pause_ratio": 0.1,
        "pause_count": 4,
        "longest_pause_sec": 1.0,
        "filler_word_count": 2,
        "words_per_minute": 120.0,
    }
    first = await client.post(
        "/voice-analysis",
        json=payload,
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    second = await client.post(
        "/voice-analysis",
        json=payload,
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["voice_analysis_id"] == second.json()["voice_analysis_id"]


@pytest.mark.asyncio
async def test_motion_analysis_ingestion_is_idempotent(client, user_id):
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

    payload = {
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
    }
    first = await client.post(
        "/motion-analysis",
        json=payload,
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    second = await client.post(
        "/motion-analysis",
        json=payload,
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["motion_analysis_id"] == second.json()["motion_analysis_id"]


@pytest.mark.asyncio
async def test_motion_first_completion(client, user_id):
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
    await client.post(
        f"/sessions/{session_id}/finish",
        headers={"X-Internal-API-Key": "test-internal-key"},
    )

    motion_payload = {
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
    }
    motion_response = await client.post(
        "/motion-analysis",
        json=motion_payload,
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert motion_response.status_code == 201

    after_motion = await client.get(
        f"/sessions/{session_id}",
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    body = after_motion.json()
    assert body["status"] == "processing"
    assert body["motion_analysis_score"] == 76.0
    assert body["overall_score"] is None

    voice_payload = {
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
    }
    voice_response = await client.post(
        "/voice-analysis",
        json=voice_payload,
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert voice_response.status_code == 201

    completed = await client.get(
        f"/sessions/{session_id}",
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    completed_body = completed.json()
    assert completed_body["status"] == "completed"
    assert completed_body["voice_analysis_score"] == 81.5
    assert completed_body["overall_score"] == 78.75


@pytest.mark.asyncio
async def test_list_sessions_by_user_route(client, user_id):
    session_id = str(uuid.uuid4())
    await client.post(
        "/sessions",
        json={
            "session_id": session_id,
            "user_id": user_id,
            "scenario_type": "public_speaking",
            "difficulty_level": "easy",
        },
        headers={"X-Internal-API-Key": "test-internal-key"},
    )

    response = await client.get(
        f"/sessions/user/{user_id}",
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["session_id"] == session_id


@pytest.mark.asyncio
async def test_users_paginated_route_not_captured_as_uuid(client, user_id):
    response = await client.get("/users/paginated?limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
