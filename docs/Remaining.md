# VirtuStage Remaining Work

Last updated: 2026-06-28

This is the authoritative backlog and verification guide. Implemented behavior is in `PROJECT_IMPLEMENTATION_STATUS.md`.

## Release Blockers

### 1. Finish the real VR lifecycle

Current problems:

- Unity sends `audio_end` and closes the socket but does not call `POST /sessions/{session_id}/finish`.
- Without finish, `end_time`, duration, `processing`, and timeout behavior are unreliable.
- CRUD can complete after both analyses even when finish has not been recorded.

Required:

1. Call finish from Unity before/alongside stream shutdown.
2. Make central/CRUD finish idempotent.
3. Store early analyses, but finalize only after `end_time` and `processing` exist.
4. Test failed/cancelled transitions.

Acceptance:

- A Quest session moves `in_progress -> processing -> completed` once.
- Timestamps and duration are correct.
- Voice-first and motion-first both work.
- Finish retries do not corrupt state or return uncontrolled errors.

### 2. Remove voice emotion inference

Emotion is absent from database/report/UI, but the voice service still loads and runs its model.

Remove from:

- `backend/Voice-Analysis-Service/app/analysis/pipeline.py`
- `backend/Voice-Analysis-Service/app/analysis/emotion_recognition.py`
- `backend/Voice-Analysis-Service/app/schemas/result.py`
- `backend/Voice-Analysis-Service/app/websocket/session_completion.py`
- `backend/Voice-Analysis-Service/requirements.txt`

Acceptance: no emotion model loads or runs; supported voice metrics and a real audio session still pass.

### 3. Make timeout terminal

Current problem: report construction can mark a component failed, but persisted session status may stay `processing`, so frontend polling can continue forever.

Required:

- Persist a terminal failure/partial-final state or make status explicitly timeout-aware.
- Add bounded frontend retry behavior.
- Refetch report when component readiness changes, not only on terminal session status.

Acceptance: missing voice, missing motion, and both-missing cases stop polling while preserving available analysis.

### 4. Protect service and VR routes

Current problems:

- Central session create/finish and analysis ingestion routes are public.
- Session creation accepts caller-provided `user_id`.

Required:

- Derive VR user identity from authenticated token.
- Require internal credentials for voice/motion callbacks.
- Never trust caller-supplied user ownership.

Acceptance: users cannot create sessions for others, and untrusted callers cannot finish sessions or submit analyses.

### 5. Normalize local configuration

Central and CRUD local `.env` files were found with different `INTERNAL_API_KEY` values.

Required: use one development value in both files and synchronized placeholders in `.env.example`. Never commit production credentials.

### 6. Run the physical release gate

The API-level gate passed. The physical flow remains:

```text
Quest login -> authenticated session -> audio/frame WebSockets -> finish
-> voice/motion callbacks -> completed report -> dashboard
```

Run it twice, including voice-first and motion-first, with no manual SQL changes.

## Unsupported Frontend Surfaces

| Surface | Missing backend | MVP action |
| --- | --- | --- |
| Notification settings | `/api/users/me/settings` | Hide or add settings table |
| Avatar upload | `/api/users/me/avatar` | Hide or add storage/avatar field |
| Scenario management | `/api/admin/scenarios` | Keep removed until modeled/enforced |
| All-in-one admin | `/api/admin` | Do not use; focused endpoints replace it |

## Presentation Upload

Status: presentation library upload/storage is implemented. VR selection/consumption and live R2 verification remain.

Recommended flow:

```text
Frontend multipart upload -> authenticated central backend
-> private Cloudflare R2 -> PostgreSQL metadata
-> owned session selection -> signed download or bounded extracted context
```

Object key:

```text
presentations/{user_id}/{file_id}/{safe_filename}
```

Implemented metadata:

```text
file_id, user_id, original_name, object_key, content_type, size_bytes,
upload_status, created_at, updated_at
```

Central APIs:

```http
GET    /api/files
POST   /api/files
GET    /api/files/{file_id}/download
DELETE /api/files/{file_id}
```

Implemented:

- Accept PDF/PPTX initially.
- Validate extension, MIME, size, and signature.
- Generate IDs/keys server-side and stream uploads.
- Use a private bucket with bucket-scoped credentials.
- Store object keys, never permanent public URLs.
- Return short-lived signed URLs after ownership checks.
- Clean up R2 objects when metadata persistence fails.
- Permanently delete both the R2 object and metadata for an owned library deletion.

Still required:

- Rotate the credentials previously exposed in prototype code; do not reuse them.
- Configure new bucket-scoped credentials in the central backend `.env`.
- Restart CRUD so `library_files` is created in the target PostgreSQL database.
- Run one live smoke flow: upload, list, signed download, delete, and confirm the object is absent in R2.
- Define how VR selects and consumes a file before adding `material_file_id` to sessions.
- Decide whether conversational context needs bounded text extraction; it is not required for storage/download.

Security:

- Cloudflare credentials shown in chat/demo code must be considered exposed and rotated before project use.
- Never hardcode account IDs, access keys, or secret keys.
- Use environment variables and least-privilege bucket credentials.

Automated coverage uses mocked R2 and verifies valid PDF/PPTX, invalid signatures/types, size limits, authentication/ownership, compensating cleanup, signed download, and permanent deletion.

## Recording Pipeline

Status: future enhancement.

The current sampled analysis streams are not a complete replay. A recording pipeline still needs timestamped audio, synchronization, interviewer/TTS policy, encoding, metadata, and storage.

Recommended lifecycle:

```text
not_requested -> capturing -> processing -> ready | failed
```

Recommended implementation:

1. Capture timestamped frames/audio independently from analysis.
2. Queue a job at session end.
3. Synchronize and encode H.264/AAC MP4 with FFmpeg.
4. Upload to private R2 and remove temporary disk files.
5. Store object key, status, duration, size, and MIME type.
6. Return signed playback after ownership checks.
7. Poll only while recording work is active.

Recording failure must not fail an analyzed session.

## Missing Tests

- Admin reading another user's session.
- User-dashboard zero and one-session aggregates.
- Concurrent voice/motion ingestion against PostgreSQL.
- Idempotent finish retry.
- Failed/cancelled lifecycle transitions.
- Timeout-aware status and polling termination.
- Browser states: loading, empty, processing, partial, failed, completed.
- Physical Quest/WebSocket release gate.
- Live private-R2 presentation smoke test with rotated credentials.
- Browser-level presentation-library interaction test.

## Recommended Order

1. Add VR finish and enforce lifecycle ordering.
2. Remove voice emotion inference.
3. Make timeout terminal and stop polling.
4. Protect service routes and derive identity from auth.
5. Normalize internal API keys and run all five services.
6. Add missing lifecycle/dashboard/authorization/concurrency tests.
7. Pass the physical Quest release gate twice.
8. Hide unfinished settings/avatar UI for MVP.
9. Configure rotated R2 credentials and run the live presentation smoke test.
10. Define VR presentation selection/consumption if required for the release.
11. Add recording after core release stability.

## Verification Commands

```powershell
cd backend\CRUD-Module
.\venv\Scripts\python.exe -m pytest -q

cd ..\central-backend
.\.venv\Scripts\python.exe -m pytest -q

cd ..\ConversationalComponent
..\central-backend\.venv\Scripts\python.exe -m pytest -q

cd ..\..
npm.cmd run typecheck
npm.cmd run build
```

With CRUD and central running against PostgreSQL:

```powershell
cd backend\central-backend
.\.venv\Scripts\python.exe tests\e2e_release_gate.py
```

For local visual dashboard data, run the idempotent seed from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\seed_demo_dashboard.ps1
```

This seed bypasses lifecycle APIs and is only for local UI/read testing. It does not replace the release gate.

## Database Workflow

New table:

1. Add SQLAlchemy model and import it before `create_all()`.
2. Add Pydantic schemas and CRUD routes.
3. Restart CRUD and verify constraints in DBeaver.
4. Add tests.

Existing table:

1. Update model/schemas.
2. Add idempotent migration in `backend/CRUD-Module/app/migrations.py`.
3. Record a unique ID in `schema_migrations`.
4. Restart CRUD twice.
5. Verify type, nullability, foreign keys, uniqueness, and indexes.
6. Run focused tests and the affected integration flow.

Do not make permanent schema changes only through DBeaver. `create_all()` does not migrate existing table structures.

## Completion Rule

A task is complete only when code/schema, validation/failure tests, applicable frontend checks, and the smallest real integration flow pass.

Core release is complete when an authenticated Quest user creates one owned session, both analyses persist, the session reaches a terminal state with explainable scores, reports/dashboards contain only real data, and the flow passes repeatedly without mock data or manual SQL edits.
