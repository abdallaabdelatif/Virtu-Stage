# Centralized Backend (CB) Implementation Plan

This document describes the architecture, phased implementation plan, and concrete tasks to build the Centralized Backend (CB) and its first submodule: Authentication. Each service (Voice Analysis, Motion Analysis, CRUD) remains standalone and communicates with the CB via HTTP/websockets. The CRUD module remains the authoritative database service.

## Assumptions
- Each analysis service posts results to the CB (HTTP or websocket). No service-level auth implemented now.
- CRUD-Module is reachable at a stable URL (e.g., `http://crud:8000`) and exposes user/session/analysis endpoints.
- CB will handle user registration/login and issue JWTs for frontend users.

---

## High-level architecture (summary)
- Frontend <-> Central Backend (auth, aggregation, dashboard)
- Central Backend <-> CRUD Service (HTTP client) — CRUD owns DB
- Analysis Services -> Central Backend (HTTP POST or websocket) — CB forwards to CRUD
- Optional: Message broker (RabbitMQ) later for resilience

---

## Phase 1 — Project scaffold & Auth submodule (priority)
Goal: Create CB FastAPI app and fully functional Authentication submodule (register, login, JWT issuance). CB will use the CRUD service to create users and to read user records for login verification.

Concrete tasks:
1. Scaffold repository
   - Create `central-backend/` with `Dockerfile`, `docker-compose.yml`, and `.env.example`.
   - Create `central-backend/app/` package.

2. Core app files
   - `app/main.py` — FastAPI app factory, include routers, startup/shutdown hooks.
   - `app/config.py` — read env, set `CRUD_BASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`.
   - `requirements.txt` — include `fastapi, uvicorn, httpx, python-jose[cryptography], pydantic, passlib, python-dotenv`.

3. CRUD client
   - `app/clients/crud_client.py` — `AsyncClient` wrapper to call CRUD endpoints: `create_user`, `get_user_by_id`, `list_users` (used to search by username/email). Add retry/backoff helper.

4. Auth submodule (deliverable)
   - `app/auth/schemas.py` — `UserRegister`, `UserLogin`, `Token`, `TokenPayload` pydantic models.
   - `app/auth/jwt.py` — JWT helpers: `create_access_token(data)`, `verify_token(token)` using HS256 and `SECRET_KEY`.
   - `app/auth/passwords.py` — `verify_password_with_crud_hash(plain, stored_hash)` to match CRUD's PBKDF2 implementation (base64(salt+digest), salt length 32 bytes, iterations 100000, hash name sha256). Implement `hash_password_for_tests()` (optional).
   - `app/auth/routes.py` — expose:
     - `POST /auth/register` : Accept `UserRegister` -> call `crud_client.create_user(payload)` -> return `201` + minimal user object (no password).
     - `POST /auth/login` : Accept `UserLogin` (username/email + password) -> fetch users via `crud_client.list_users()` and find matching username/email -> verify password with `verify_password_with_crud_hash` -> issue `access_token` (JWT) and `refresh_token` (optional).
   - `app/auth/deps.py` — `get_current_user` dependency: verify JWT and attach user info (call CRUD `GET /users/{id}` if needed).

5. Tests & docs for auth
   - `tests/test_auth.py` — unit tests for JWT creation/verification and password verification logic using sample hashed password from CRUD patterns.
   - `docs/auth.md` — short usage (curl) examples for register & login.

Acceptance criteria for Phase 1
- `POST /auth/register` creates a new user through CRUD and returns created user (no password).
- `POST /auth/login` returns a valid JWT when provided correct credentials.
- `GET /` health check present.

---

## Phase 2 — Internal analysis ingestion & forwarding
Goal: CB receives analysis results from services and persists them (via CRUD).

Concrete tasks:
1. Internal ingestion routes
   - `app/api/analysis.py`:
     - `POST /internal/analysis/voice` — accept the VoiceAnalysis payload (the payload shape used by Voice-Analysis-Service) -> validate -> forward to CRUD `/voice-analysis` (router in CRUD-Module uses `/voice-analysis`) using `crud_client`.
     - `POST /internal/analysis/motion` — same for Motion.

2. Add simple retry and local queue fallback
   - If forwarding to CRUD fails, store payload in a local file-based queue for retry.

3. Update Voice-Analysis-Service config
   - Point `CENTRALIZED_BACKEND_URL` to CB base URL and ensure path matches (`/internal/analysis/voice`).

Acceptance criteria
- CB receives posted analysis JSON and CRUD records are created.

---

## Phase 3 — Dashboard endpoints & session orchestration
Goal: Implement dashboard-facing endpoints to manage sessions and see aggregated results.

Concrete tasks:
1. Implement routers in `app/api/`:
   - `GET /dashboard/sessions` — uses CRUD client to list sessions (paginated), adds auth dependency.
   - `POST /dashboard/sessions/{session_id}/start` — triggers session start event (publish to broker or call analysis services via their HTTP start endpoint, if available).

2. Websocket support for real-time updates (optional):
   - `/ws/dashboard/updates` — push analysis completion notifications to authenticated dashboards.

Acceptance criteria
- Dashboard endpoints available and protected by `get_current_user` dependency.

---

## Phase 4 — Hardening, deployment & observability
Tasks:
- Add docker-compose to run CB + CRUD + Voice + Motion + (optional) RabbitMQ for resilience.
- Add logging, metrics (Prometheus), and health checks.
- Add idempotency checks and dedupe on session_id when forwarding to CRUD.
- Replace local queue with a broker publish/subscribe model.

---

## File / folder proposed layout (central-backend)
```
central-backend/
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example
├─ requirements.txt
├─ app/
│  ├─ __init__.py
  │  ├─ main.py
  │  ├─ config.py
  │  ├─ clients/
  │  │  └─ crud_client.py
  │  ├─ auth/
  │  │  ├─ schemas.py
  │  │  ├─ jwt.py
  │  │  ├─ passwords.py
  │  │  ├─ routes.py
  │  │  └─ deps.py
  │  ├─ api/
  │  │  └─ analysis.py
  │  ├─ websocket/
  │  └─ utils/
  │     ├─ logging.py
  │     └─ retry.py
  └─ tests/
```

---

## Notes and small decisions
- For `login` the CB will call CRUD's `GET /users` listing and match by username/email (this is acceptable initially). Later, add `GET /users/by-username` to CRUD for efficiency.
- Password verification: replicate CRUD's `salt + pbkdf2_hmac('sha256', iterations=100000)` base64 format.
- Token format: JWT HS256 signed with `SECRET_KEY`. Use `python-jose` for RS256 upgrade later.

---

## Quick start (developer commands)
1. From repo root (dev):
```powershell
cd central-backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9000
```

2. Env vars (example in `.env.example`):
```
CRUD_BASE_URL=http://crud:8000
CENTRAL_HOST=0.0.0.0
CENTRAL_PORT=9000
SECRET_KEY=super-secret-change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

If you want I can now scaffold the `central-backend` repo structure and implement Phase 1 (auth) with tests and a small integration example using the existing `CRUD-Module`. Which would you like me to generate now? 

---

## Guideline: Route all future API endpoints through the Central Backend
When you add any new API (for dashboard actions, analysis ingestion, or admin tasks), follow this minimal pattern so every client talks to the Central Backend (CB) and the CB enforces auth, validation, and persistence.

1. Define the contract
   - Create a small OpenAPI schema or Pydantic model in `central-backend/app/api/schemas/` describing request and response shapes.
   - Add example payloads and validation rules.

2. Expose the route in CB
   - Add an APIRouter under `central-backend/app/api/` and implement the endpoint.
   - Keep public routes under `/auth` only; all other routes will be protected by the CB middleware (or use `Depends(get_current_user)` for per-route control).

3. Forwarding and persistence
   - If the operation modifies or reads persistent data, forward the normalized payload to the CRUD service via `app/clients/crud_client.py` and handle CRUD responses.
   - Prefer idempotent operations (use `session_id` or an `idempotency_key`). If forwarding, include that key so CRUD can dedupe.

4. Error handling and retries
   - For transient CRUD failures, return a 502 to clients and enqueue the request for retry (simple file queue or broker later).
   - Log and return structured errors (include `error_code` and `reason`).

5. Observability and audit
   - Log requests, user id (from token `sub`), and correlation id. Emit metrics for success/failure and latency.

6. Security
   - Require Bearer JWT on all non-public endpoints. Validate token and check `sub` user exists (middleware already implemented).
   - Sanitize and validate incoming data before forwarding to CRUD.

7. Testing
   - Add unit tests for the router (schema validation) and integration tests that spin up CB + CRUD and assert end-to-end behavior.

8. Example (create voice analysis via CB)
   - Route: `POST /internal/analysis/voice` (protected)
   - Body: `VoiceAnalysisCreate` Pydantic model under `app/api/schemas/`.
   - CB handler: validate -> add `received_at` and `source=voice-service` -> forward to `POST {CRUD_BASE_URL}/voice-analysis` -> return CRUD response to caller.

Following this pattern keeps a single, authenticated entrypoint for all clients and centralizes validation, monitoring, and orchestration.
