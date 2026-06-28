# VirtuStage Implementation Status

Last verified: 2026-06-28

This is the authoritative reference for implemented work, exposed APIs, important files, database state, and verification. Pending work is in `PROJECT_REMAINING_WORK.md`.

## Current Status

The authenticated API journey works against local PostgreSQL:

```text
register -> empty dashboard -> create VR session -> finish session
-> voice-first partial report -> motion result -> completed report
-> updated session list and dashboard
```

The live release gate returned concurrent registration `201/409`, final session `completed`, report `complete`, overall score `78.75`, and dashboard session count `1`. It cleaned up its test account.

The authenticated presentation library and conversion pipeline are implemented end to end in code: PDF pages render to PNG; PPTX converts through Gotenberg and then renders to PNG; originals and generated images use private R2 storage; PostgreSQL stores ordered slide metadata; metadata listing does not download images; selecting a presentation returns short-lived signed slide URLs; deletion removes all generated images, the original, and metadata. Automated API tests use a mocked R2 boundary; a live R2 smoke test awaits newly rotated credentials.

The project is not fully release-ready because Unity still does not call finish, timeout does not terminate polling, and the physical Quest/WebSocket flow has not passed the release gate.

## Architecture

```text
React frontend (5173)
        |
        v
Central backend (9000)
        |
        +-> CRUD/PostgreSQL (8000 / PostgreSQL 5432)
        +-> Voice analysis (8001)
        +-> Conversational component (8002)
        +-> Motion analysis (9001)
        +-> Gotenberg (PPTX -> PDF)
        +-> Private Cloudflare R2 (originals and generated PNG slides)
```

- Browser traffic goes through central backend.
- CRUD and analysis services are internal.
- PostgreSQL is the source of truth.
- Voice and motion may finish in either order.
- The browser uses HTTP polling for session status.

## Product Decisions

- Voice report: speech rate, fillers, pauses, confidence, clarity, focus, anxiety.
- Remove emotion labels, dominant emotion, and emotion timeline.
- Motion report: posture, gaze proxy, gestures, composure, stability, fidgeting, nervousness, and rule-generated recommendations.
- Do not claim exact eye contact.
- Remove unsupported pitch, volume, context, hardware, AI-engine, replay, and mock deltas.
- Presentation library conversion and the VR on-selection image contract are implemented. Persisting a selected `file_id` on a training session remains a separate product decision.

## Implemented Changes

### Authentication and accounts

- Register/login/current user, password reset/change, profile update, account deletion.
- Strong password rules in central and CRUD.
- Matching username validation in central, CRUD, and frontend.
- Lowercase email normalization.
- Case-insensitive username/email uniqueness, lookup, and login.
- Controlled `409` for duplicate and insert-race registration.

Files:

- `backend/central-backend/app/auth/routes.py`
- `backend/central-backend/app/auth/schemas.py`
- `backend/CRUD-Module/app/routers/user.py`
- `backend/CRUD-Module/app/routers/auth.py`
- `backend/CRUD-Module/app/schemas/user.py`
- `app/routes/register.tsx`
- `app/utils/accountValidation.ts`

### Session lifecycle and scoring

```text
create -> in_progress
finish -> processing
both analyses -> completed
other terminal values -> failed | cancelled
```

```text
voice_score = average(confidence, clarity, focus, 1 - anxiety) * 100
overall_score = average(voice_score, motion_score)
```

- Start/end timestamps and component/overall scores persist on the session.
- Sequential duplicate analysis ingestion returns the existing row.
- Unique indexes enforce one voice and one motion row per session.

Files:

- `backend/CRUD-Module/app/models/session.py`
- `backend/CRUD-Module/app/routers/session.py`
- `backend/CRUD-Module/app/services/session_scoring.py`
- `backend/CRUD-Module/app/routers/voice_analysis.py`
- `backend/CRUD-Module/app/routers/motion_analysis.py`
- `backend/central-backend/app/api/vr.py`

### Session/report APIs

- Current-user list and owned detail.
- Status plus voice/motion readiness.
- Stable processing, complete, partial, and failed report responses.
- Voice-first, motion-first, completion, timeout, ownership, and admin bypass.

Files:

- `backend/central-backend/app/api/sessions.py`
- `backend/central-backend/app/api/schemas/sessions.py`
- `backend/central-backend/app/services/session_report.py`
- `backend/central-backend/tests/test_api_sessions.py`

### Dashboards and admin

- User totals, averages, improvement, score history, voice/motion history.
- Admin totals, sessions today, score/activity history, registrations, user list.
- Enable/disable users.
- Unsupported audit activity and scenario controls removed.

Files:

- `backend/CRUD-Module/app/services/dashboard_aggregates.py`
- `backend/CRUD-Module/app/routers/aggregates.py`
- `backend/central-backend/app/api/dashboard.py`
- `backend/central-backend/app/api/admin.py`
- `app/mappers/dashboardMapper.ts`
- `app/components/UserDashboard.tsx`
- `app/components/AdminDashboard.tsx`
- `app/routes/admin.tsx`

### Frontend sessions and report

- Real session/analytics lists and report.
- Separate `In Progress` and `Processing Analysis` labels.
- Three-second polling for non-terminal sessions.
- Independent voice/motion pending and failed states.
- Flat motion assessment mapping with strengths/growth/recommendations.
- Unsupported report sections and replay removed.

Files:

- `app/services/sessionService.ts`
- `app/services/analyticsService.ts`
- `app/hooks/useSessionPolling.ts`
- `app/mappers/sessionMapper.ts`
- `app/mappers/sessionReportMapper.ts`
- `app/routes/sessions.tsx`
- `app/routes/analytics.tsx`
- `app/routes/session.analytics.tsx`
- `app/routes/session.$id.tsx`

### Presentation library

- Authenticated users can upload, list, open, retry, and permanently delete their own presentations.
- Upload accepts PDF/PPTX only, with a 50 MB limit and extension, MIME, and file-signature validation.
- Server-generated keys follow `presentations/{user_id}/{file_id}/{safe_filename}`.
- PDF pages render to 1920-pixel-wide PNG files with PyMuPDF.
- PPTX files convert to PDF through Gotenberg, then use the same rendering path.
- Generated keys follow `presentations/{user_id}/{file_id}/slides/0001.png`.
- Objects remain private in R2; the database stores ordered object keys and dimensions rather than public URLs.
- Metadata lists contain no image URLs. The slide manifest signs URLs only after the user/VR client selects an owned, ready presentation.
- Original and slide downloads use short-lived signed URLs after ownership verification.
- Processing states are `queued`, `processing`, `ready`, and `failed`; the frontend polls active work and can retry failures.
- Deletion removes every generated slide and the original in one R2 batch request, then removes PostgreSQL metadata. It also removes stale metadata when an object was manually deleted from R2, serializes against in-process conversion, and uses a 120-second frontend timeout.
- Failed metadata persistence triggers compensating R2 deletion.
- Partial slide-upload failure removes images already written for that attempt.
- The frontend uses real upload progress, a 120-second upload timeout, DTO mapping, processing state/count, retry, and an owned-download action.
- Deletion keeps the card visible in a disabled `Deleting...` state and removes it only after backend confirmation; failed deletion restores the normal controls.

Files:

- `backend/CRUD-Module/app/models/library_file.py`
- `backend/CRUD-Module/app/models/presentation_slide.py`
- `backend/CRUD-Module/app/schemas/library_file.py`
- `backend/CRUD-Module/app/routers/library_file.py`
- `backend/central-backend/app/api/files.py`
- `backend/central-backend/app/api/schemas/files.py`
- `backend/central-backend/app/services/file_storage.py`
- `backend/central-backend/app/services/presentation_processing.py`
- `backend/central-backend/app/clients/crud_client.py`
- `app/routes/library.tsx`
- `app/services/libraryService.ts`
- `app/mappers/libraryMapper.ts`
- `app/types/library.ts`
- `backend/CRUD-Module/tests/test_library_files.py`
- `backend/central-backend/tests/test_api_files.py`
- `backend/docs/VR/presentation-library-integration.md`

### VR defaults

`backend/VR/BackendClient.cs.txt` and `FrameWebsocketStreamer.cs.txt` target central port `9000`. The host IP remains environment-specific.

## Exposed Central APIs

### Authentication/account

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Register and return token/user |
| `POST` | `/api/auth/login` | Login by username/email |
| `GET` | `/api/auth/me` | Current user |
| `POST` | `/api/auth/forgot-password` | Request reset |
| `POST` | `/api/auth/reset-password` | Reset password |
| `PATCH` | `/api/users/me` | Update profile |
| `PATCH` | `/api/users/me/password` | Change password |
| `DELETE` | `/api/users/me` | Delete account |

### Sessions/reports

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/sessions/me` | Current user's sessions |
| `GET` | `/api/sessions/{session_id}` | Owned detail |
| `GET` | `/api/sessions/{session_id}/status` | Poll status/readiness |
| `GET` | `/api/sessions/{session_id}/report` | Combined persisted report |

Status shape:

```json
{"session_id":"uuid","status":"processing","voice_ready":true,"motion_ready":false}
```

Report top-level shape:

```json
{
  "report_status": "processing",
  "voice_status": "ready",
  "motion_status": "pending",
  "session": {},
  "voice_analysis": {},
  "motion_analysis": null
}
```

### Dashboard/admin

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/dashboard/me` | User aggregates |
| `GET` | `/api/admin/dashboard` | Platform aggregates |
| `GET` | `/api/admin/users` | Admin user list |
| `PATCH` | `/api/admin/users/{user_id}/status` | Enable/disable user |

### Presentation library

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/files` | List the current user's presentations |
| `POST` | `/api/files` | Validate/upload PDF/PPTX and schedule conversion |
| `GET` | `/api/files/{file_id}/status` | Get current conversion status |
| `POST` | `/api/files/{file_id}/retry` | Retry queued/failed conversion |
| `GET` | `/api/files/{file_id}/slides` | Return ordered signed PNG URLs after selection |
| `GET` | `/api/files/{file_id}/download` | Return an owned signed URL for the original |
| `DELETE` | `/api/files/{file_id}` | Delete generated PNGs, original, and metadata |

### VR/analysis

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/sessions` | Create VR session |
| `POST` | `/sessions/{session_id}/finish` | Finish capture |
| `POST` | `/voice-analyses` | Ingest voice result |
| `POST` | `/motion-analyses` | Ingest motion result |
| `WS` | `/ws/vr/audio/{session_id}` | Proxy VR audio |
| `WS` | `/ws/vr/frames/{session_id}` | Proxy VR frames |

These ingestion/session routes still need stronger service authentication.

## Internal CRUD APIs

Central calls CRUD for users, sessions, analyses, conversation history, library-file metadata, internal login/account operations, password-reset tokens, and dashboard/admin aggregates. Protected internal routes use `X-Internal-API-Key`; central and CRUD `.env` values must match.

## Frontend Endpoint State

Connected: auth/account, sessions/status/report, presentation library, user dashboard, admin dashboard/users/status.

Configured but not implemented centrally:

- `/api/users/me/settings`
- `/api/users/me/avatar`
- `/api/admin`
- `/api/admin/scenarios`

## Database State

```text
container: virtustage-postgres
PostgreSQL: 16
host/port: localhost:5432
database/user: virtustage
volume: virtustage_postgres_data
```

Tables:

- `users`
- `training_sessions`
- `voice_analysis`
- `motion_analysis`
- `conversation_histories`
- `password_reset_tokens`
- `schema_migrations`
- `library_files`
- `presentation_slides`

Migrations:

- `20260623_core_auth`
- `20260625_motion_presentation_assessment`
- `20260628_remove_voice_emotion_fields`
- `20260628_session_processing_status`
- `20260628_registration_identity_uniqueness`
- `20260628_presentation_processing`

Verified: analysis-per-session uniqueness, case-insensitive user identity, removed emotion columns, session timestamps/scores, and library-file ownership/metadata behavior. The `library_files` table is created by SQLAlchemy `create_all()` on CRUD startup; restart CRUD before a live PostgreSQL/R2 smoke test.

## Local Startup

```powershell
docker start virtustage-postgres

cd "S:\SeniorLevel\GP\Phase2\Dashboard\virtustage-dashboard\backend\CRUD-Module"
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

In another terminal:

```powershell
cd "S:\SeniorLevel\GP\Phase2\Dashboard\virtustage-dashboard\backend\central-backend"
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 9000
```

Frontend:

```powershell
cd "S:\SeniorLevel\GP\Phase2\Dashboard\virtustage-dashboard"
npm run dev
```

Set the same `INTERNAL_API_KEY` in central and CRUD `.env` files.

For presentation storage, also set `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, and optionally `R2_SIGNED_URL_EXPIRES_SECONDS` in the central backend `.env`. Use a private bucket and newly rotated bucket-scoped credentials. Run `docker compose up -d gotenberg` from `backend/central-backend`; local central uses `GOTENBERG_URL=http://localhost:3001`.

## Demo Dashboard Seed

Reusable script:

```text
scripts/seed_demo_dashboard.ps1
```

It creates one login-capable development user with five completed sessions and matching voice/motion analysis rows. Rerunning it replaces only this dedicated demo account, so it is safe for repeated local dashboard testing.

Run from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\seed_demo_dashboard.ps1
```

Demo login:

```text
username: dashboard_demo
email: dashboard.demo@example.com
password: Demo@1234
```

Seeded result:

```text
completed sessions: 5
voice analyses: 5
motion analyses: 5
average overall score: 78.60
```

Prerequisites:

1. Docker Desktop is running.
2. The `virtustage-postgres` container exists; the script starts it when stopped.
3. CRUD has been started at least once so current tables/migrations exist.
4. To view the dashboard, start CRUD on `8000`, central on `9000`, and frontend on `5173`.
5. Central and CRUD must use the same `INTERNAL_API_KEY`.

Five sessions populate totals, averages, charts, session lists, and reports. Improvement remains unavailable by design because its formula requires ten completed sessions.

## DBeaver

Use PostgreSQL at `localhost:5432`, database/user `virtustage`, username/password auth, SSL disabled.

```sql
SELECT current_database(), current_user, version();

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

SELECT * FROM schema_migrations ORDER BY applied_at;
```

Create users through the API. Direct SQL can support temporary rendering/read tests, but it does not prove validation, lifecycle, scoring, or idempotency.

## Verification

| Check | Result |
| --- | --- |
| Central backend | 32 passed |
| CRUD module | 17 passed |
| Conversational bridge | 3 passed |
| Frontend typecheck/build | Passed |
| Presentation API with mocked R2 | 13 passed (PDF/PPTX branches, manifest, ordering, ownership, retry/cleanup, stale metadata deletion) |
| Live R2 smoke test | Pending rotated credentials |
| Real Gotenberg/PyMuPDF sample | Passed: 41 ordered 1920x1080 slides |
| PostgreSQL migrations/indexes | Verified |
| Flat motion mapper | Passed |
| Register-to-dashboard API release gate | Passed |

Reusable release gate: `backend/central-backend/tests/e2e_release_gate.py`.
