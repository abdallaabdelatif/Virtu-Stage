# VirtuStage Testing Coverage

This document summarizes the implemented testing coverage for Chapter 6: Testing and Evaluation.

## Current Result

The automated test suite currently contains **87 passing test cases**:

- **52 Central Backend tests** using `pytest` and `allure-pytest`
- **35 frontend tests** using `Vitest`, React Testing Library, and `allure-vitest`

Central Backend is the primary automated backend testing target because it is the orchestration layer between the dashboard, CRUD service, VR sessions, storage, voice analysis, motion analysis, and conversational services. This does **not** mean the other services cannot be tested; it means they are currently covered mainly through Central Backend integration boundaries and service health/test endpoints.

Latest verified backend command:

```powershell
cd backend\central-backend
.\.venv\Scripts\python.exe -m pytest --alluredir=allure-results
```

Latest result:

```text
52 passed
0 failed
0 skipped
```

Latest verified frontend command:

```powershell
npm.cmd run test
```

Latest result:

```text
10 test files passed
35 tests passed
0 failed
0 skipped
```

Backend Allure report command:

```powershell
allure serve allure-results
```

Frontend Allure report command:

```powershell
allure serve allure-results\frontend
```

## Is This Enough?

For the current project scope, **87 automated tests plus Postman API testing is enough for documentation and graduation evaluation**, because the tests cover the system's most important user-facing, service-facing, and UI-facing behavior:

- Authentication and account management
- Protected route authorization
- Frontend auth forms and route guards
- Auth context token/session behavior
- Frontend service calls and DTO mappers
- Dashboard, sessions, library, and admin page states
- Frontend error handling
- Dashboard and admin APIs
- Session listing, ownership, status, and report states
- VR session creation and validation
- Voice and motion analysis ingestion
- File upload, validation, processing, cleanup, and slide retrieval
- Avatar upload and public avatar retrieval
- WebSocket proxy client behavior
- Negative cases such as invalid token, duplicate account data, weak password, invalid files, forbidden access, and bad internal API key

The coverage is strongest around Central Backend correctness, API behavior, integration boundaries, frontend data mapping, frontend route protection, and negative/security validation. The remaining testing areas are mostly direct per-service test suites, full-browser E2E, hardware, deployment, or external-service dependent.

## Service-Level Testing Scope

VirtuStage is a multi-service system. The current automated tests are concentrated in the dashboard frontend and Central Backend, while the other backend services are verified indirectly or through service-level runtime checks.

| Service / Layer | Current Coverage | Meaning |
|---|---|---|
| Frontend Dashboard | Direct automated tests | Vitest tests cover auth pages, route protection, context behavior, service calls, mappers, page states, UI components, and error handling |
| Central Backend | Direct automated tests | Pytest tests cover APIs, authentication, sessions, files, dashboard/admin, VR session logic, voice/motion ingestion, storage boundaries, and negative/security cases |
| CRUD Service | Indirectly covered through Central Backend tests and Postman flows | Central Backend tests mock or validate calls that depend on CRUD behavior; CRUD can still have its own direct tests for database models, duplicate users, auth records, sessions, and `/test` or `/health` routes |
| Conversational Service | Partially covered through Central Backend proxy/client tests | WebSocket proxy behavior is tested at the Central Backend boundary; full direct testing would require service-specific WebSocket tests |
| Voice Analysis Service | Partially covered through Central Backend ingestion/proxy tests | Central Backend verifies forwarding and internal-key protection; direct model-quality testing requires real or sample audio inputs |
| Motion Analysis Service | Partially covered through Central Backend ingestion tests | Central Backend verifies forwarding and internal-key protection; direct model-quality testing requires frame/camera/VR motion samples |
| Storage / File Processing | Directly covered at Central Backend boundary with mocked storage/conversion | Upload validation, cleanup, status, download, slide manifest, and processing failure behavior are tested without requiring real cloud credentials |

The difference between a `/test` endpoint and an automated test suite is important:

- A `/test` or `/health` endpoint checks that a running service is reachable or that one runtime path works.
- A `tests/` folder with `pytest`, `Vitest`, or similar tools contains repeatable automated test cases that can be executed locally or in CI.

Therefore, if CRUD, Conversational, Voice, or Motion services include `/test` endpoints, those endpoints are useful for smoke testing, but they do not replace a full automated unit/integration test suite for those services.

## Automated Central Backend Test Breakdown

| Test Area | Test File | Number of Tests | Main Coverage |
|---|---:|---:|---|
| Account and protected routes | `backend/central-backend/tests/test_api_account.py` | 5 | Protected route, missing token, profile update, invalid password, account deletion cleanup |
| Authentication | `backend/central-backend/tests/test_api_auth.py` | 6 | Registration validation, duplicate email, duplicate username, weak password, invalid login |
| Avatars | `backend/central-backend/tests/test_api_avatars.py` | 4 | Avatar normalization, spoofed image rejection, public avatar read, missing avatar |
| Dashboard and admin | `backend/central-backend/tests/test_api_dashboard.py` | 5 | User dashboard, admin dashboard, admin user list, admin delete restrictions |
| Files and presentation processing | `backend/central-backend/tests/test_api_files.py` | 13 | PDF/PPTX upload, invalid files, download, delete, slide manifest, processing failure cleanup |
| Sessions and reports | `backend/central-backend/tests/test_api_sessions.py` | 7 | Session ownership, partial report, complete report, failed report, voice/motion readiness |
| VR, voice, and motion APIs | `backend/central-backend/tests/test_api_vr.py` | 10 | VR session create, duplicate session, invalid mode, voice ingestion, motion ingestion, internal key checks |
| Service proxy clients | `backend/central-backend/tests/test_clients.py` | 2 | Conversational proxy and voice-analysis WebSocket proxy behavior |
| **Total** |  | **52** |  |

## Automated Frontend Test Breakdown

| Test Area | Test File | Number of Tests | Main Coverage |
|---|---:|---:|---|
| Auth pages | `app/routes/authPages.test.tsx` | 6 | Login validation, login success, register validation, register success, forgot password, reset password |
| Protected routes | `app/components/ProtectedRoute.test.tsx` | 4 | Redirect unauthenticated users, inactive users, wrong role users, allow matching role |
| Auth context | `app/context/AuthContext.test.tsx` | 4 | Token loading, current user verification, login/update/logout, failed verification cleanup |
| Frontend services | `app/services/frontendServices.test.ts` | 6 | Auth, session, dashboard, library upload, file list, download URL service calls |
| DTO mappers | `app/mappers/frontendMappers.test.ts` | 4 | User, session, dashboard, admin user, and library file mapping |
| Page states | `app/routes/pageStates.test.tsx` | 4 | Dashboard data rendering, empty sessions, library upload validation, admin users |
| Error handling | `app/utils/apiError.test.ts` | 2 | API error messages and unauthorized notification |
| Account validation | `app/utils/accountValidation.test.ts` | 2 | Username and password validation |
| UI components | `app/components/Input.test.tsx`, `app/components/SessionTable.test.tsx` | 3 | Input accessibility and session table rendering |
| **Total** |  | **35** |  |

## Unit Testing

Purpose: test isolated functions and UI components without running the full application.

Evidence:

- `app/mappers/frontendMappers.test.ts`
  - Verifies DTO mapping for users, sessions, dashboard stats, admin users, and files.
- `app/utils/apiError.test.ts`
  - Verifies API error message extraction and unauthorized handling.
- `app/utils/accountValidation.test.ts`
  - Validates username rules.
  - Validates password strength rules.
- `app/components/Input.test.tsx`
  - Verifies label accessibility.
  - Verifies native input attributes and change events.
- `app/components/SessionTable.test.tsx`
  - Verifies session table rendering behavior.

Run:

```powershell
npm.cmd run test
```

## API Testing

Purpose: test HTTP endpoints from the client side using real requests against the running Central Backend.

Evidence:

- `API Tests.postman_collection.json`
  - Auth: register, login, current user, forgot/reset password.
  - Protected routes: bearer token access.
  - Dashboard: authenticated user dashboard.
  - Sessions: create, duplicate, invalid mode, list, detail, status, report, finish.
  - Files: list, upload, status, slides, download, retry, delete.
  - Internal ingestion: voice and motion analysis payloads.
  - Admin: dashboard, users, status update, delete user.
  - Negative cases: missing token, invalid password, bad internal API key, duplicate account data.

Run:

1. Start CRUD Module on port `8000`.
2. Start Central Backend on port `9000`.
3. Import `API Tests.postman_collection.json` into Postman.
4. Run requests manually in the safe order: health, register, login, current user, protected route, dashboard, duplicate/invalid auth cases, session APIs, then optional file/admin/internal tests.

## Integration Testing

Purpose: test that Central Backend logic integrates correctly with CRUD, voice, motion, conversational, and storage boundaries.

Evidence:

- `test_api_sessions.py`
  - Session ownership and report composition.
  - Voice-ready, motion-ready, partial, complete, and failed report states.
- `test_api_files.py`
  - Upload, list, download, delete, slide manifest, invalid file validation.
  - Storage cleanup when metadata or processing fails.
  - PDF/PPTX processing behavior with mocked storage/conversion.
- `test_api_vr.py`
  - VR session creation.
  - Voice analysis ingestion forwarding.
  - Motion analysis ingestion forwarding.
  - Session cleanup logic for active audio/frame streams.
- `test_clients.py`
  - Conversational and voice WebSocket proxy connection/forwarding behavior.

Run:

```powershell
cd backend\central-backend
.\.venv\Scripts\python.exe -m pytest
```

## Negative Testing

Purpose: verify that the system rejects invalid inputs and unauthorized requests safely.

Evidence:

- `test_api_auth.py`
  - Invalid username rejected before CRUD call.
  - Weak password rejected before CRUD call.
  - Duplicate email conflict returned.
  - Duplicate username conflict returned.
  - Invalid login rejected.
- `test_api_account.py`
  - Protected route rejects missing token.
  - Invalid current password is rejected.
  - Account deletion removes avatar data.
- `test_api_vr.py`
  - Session creation requires bearer token.
  - Duplicate VR session rejected.
  - Invalid VR mode rejected.
  - Voice analysis requires internal API key.
  - Motion analysis requires internal API key.
- `API Tests.postman_collection.json`
  - Missing token.
  - Bad internal API key.
  - Duplicate account data.
  - Invalid email, username, password, and reset token.

## Allure Reporting

The backend pytest suite and frontend Vitest suite are configured for Allure reporting.

Backend metadata:

- Epic: `VirtuStage Backend Testing`
- Features: authentication, account management, VR session API, session reports, presentation files, dashboard/admin, avatars, and service proxies
- Stories: route-specific behavior such as duplicate email validation, motion analysis ingestion, report states, and storage cleanup
- Severity: critical for security/negative cases and normal for standard happy-path behavior

Frontend metadata:

- Reporter: `allure-vitest/reporter`
- Result directory: `allure-results/frontend`
- Features/stories include auth pages, protected routes, auth context, service calls, DTO mapping, page states, and error handling

Allure is useful for Chapter 6 because it provides a visual summary of:

- Total test cases
- Pass/fail percentage
- Test suites
- Features and stories
- Execution duration
- Failure details if any test fails

## Remaining Testing Work

The following tests are not fully automated because they require a browser workflow, hardware, external services, credentials, or deployed infrastructure:

| Remaining Test Type | Reason |
|---|---|
| Direct CRUD service test suite | Requires adding service-local tests for database models, auth records, duplicate user handling, CRUD validation, and service routes |
| Direct Conversational service test suite | Requires WebSocket-level tests against the conversational service itself |
| Direct Voice Analysis service test suite | Requires service-local tests with sample audio and expected analysis outputs |
| Direct Motion Analysis service test suite | Requires service-local tests with frame/motion samples and expected analysis outputs |
| Full frontend E2E browser flow | Requires Playwright/Cypress test setup and a running frontend plus backend |
| Real VR headset end-to-end test | Requires Unity/VR client and headset runtime |
| Real WebSocket audio/frame streaming | Requires live audio and frame stream from VR client |
| Real voice model evaluation | Requires real audio input and Voice Analysis Service |
| Real motion model evaluation | Requires camera/VR frame input and Motion Analysis Service |
| Real cloud storage integration | Requires valid Cloudflare R2 credentials |
| Production deployment test | Requires Railway/Vercel deployed environment |
| Load/performance testing | Requires concurrent users and controlled benchmark setup |

## Recommended Chapter 6 Statement

The system was validated using **87 automated tests with Allure reporting**, plus Postman API tests. The Central Backend was selected as the primary backend testing target because it orchestrates authentication, account management, protected APIs, dashboard/admin APIs, sessions, reports, presentation files, avatars, VR session APIs, voice-analysis ingestion, motion-analysis ingestion, WebSocket proxy clients, and negative/security cases. The frontend tests cover auth pages, protected routes, auth context behavior, service calls, DTO mapping, dashboard/session/library/admin page states, UI components, and error handling. CRUD, Conversational, Voice Analysis, and Motion Analysis services are currently verified mainly through Central Backend integration boundaries, mocks, and service health/test endpoints. Remaining tests such as direct service-local test suites, full browser E2E flows, full VR headset streaming, live AI model evaluation, and production-scale performance testing are environment-dependent and were identified as limitations or future testing work.
