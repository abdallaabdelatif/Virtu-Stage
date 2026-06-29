# Backend Railway changes: what changed and why

This document explains the production-deployment changes made to the backend.
The Vercel dashboard application was not modified.

## Resulting architecture

```text
Dashboard / VR App
        |
        | HTTPS + WSS, Bearer JWT
        v
Central Backend
   |       |       |       |
   |       |       |       +--> Conversational AI
   |       |       +----------> Motion Analysis
   |       +------------------> Voice Analysis
   |
   +--> CRUD Module --> Railway PostgreSQL

Voice / Motion / Conversational events return through Central Backend.
The frontend and VR app never call CRUD or analysis workers directly.
```

Central Backend remains the public gateway. CRUD and the three worker services
are intended to be private Railway services.

## Changes shared by all five services

- Added or updated a production `Dockerfile` using Python 3.11.
- Every process reads Railway's dynamic `$PORT`; no application production port
  is embedded in a Dockerfile.
- Containers run as a non-root `app` user.
- Added a `railway.toml` using the Dockerfile builder.
- Added a dedicated `GET /health` route and configured it as the Railway
  healthcheck.
- Updated `.env.example` and README deployment instructions.
- Added production checks that reject default development secrets.
- Documented private Railway networking and exact root/config paths in
  `RAILWAY_DEPLOYMENT.md`.

## Central Backend changes

### Service communication

Central Backend still performs these outbound calls:

- `CRUD_BASE_URL` for all persistence.
- `VOICE_ANALYSIS_WS_URL` for the private Voice audio and transcript WebSockets.
- `MOTION_ANALYSIS_WS_URL` for the private Motion frame WebSocket.
- `CONVERSATIONAL_COMPONENT_WS_URL` for the private conversation WebSocket.

It does not receive `DATABASE_URL` and does not connect to PostgreSQL.

### New Conversational-to-Central transcript route

Added:

```text
WS /ws/internal/voice-analysis/transcript/{session_id}
```

Previously, Conversational AI connected directly to Voice Analysis to forward
transcripts. It now sends transcript events to Central Backend. Central validates
the shared internal key and relays those events to Voice Analysis.

Reason: this enforces the requested boundary that worker events pass through
Central Backend and prevents Conversational AI from owning another worker's
private service URL.

### Worker callback authentication

These routes now require `X-Internal-API-Key`:

```text
POST /voice-analyses
POST /motion-analyses
```

They remain outside user JWT authentication because they are service callbacks,
but they are no longer anonymous public write endpoints.

### VR authentication and ownership

The following are no longer anonymous:

```text
POST /sessions
POST /sessions/{session_id}/finish
WS /ws/vr/audio/{session_id}
WS /ws/vr/frames/{session_id}
```

- Session HTTP routes require a Bearer JWT.
- Both VR WebSockets validate the Bearer JWT already sent by the Unity code.
- WebSocket access is limited to the user who created the session.
- The authenticated JWT user ID is used for persistence; the client can no
  longer create a session for an arbitrary user ID.
- Session creation returns an error if the CRUD training-session record cannot
  be created. Previously, that error was logged while the API still returned a
  successful in-memory session, which could later break analysis foreign keys.

### Production secret validation

When `ENVIRONMENT=production`, startup fails if:

- `SECRET_KEY` is the development value or shorter than 32 characters.
- `INTERNAL_API_KEY` is the development value or shorter than 32 characters.

This prevents an accidentally deployed default JWT or internal-service secret.

### Removed Central Backend variables

#### `CENTRALIZED_BACKEND_URL`

Removed from Central Backend only. Central does not need to call itself. Voice
and Motion still use their own `CENTRALIZED_BACKEND_URL` to post results to
Central.

#### `VOICE_ANALYSIS_RESULT_CALLBACK_URL`

Removed from Central Backend. Previously Central placed a callback URL in the
Voice WebSocket query string. Voice now owns its callback configuration through
its environment, which avoids accepting a caller-controlled callback URL and
makes the production contract clearer.

#### `VIDEO_ANALYSIS_WS_URL`

Removed because it was only a legacy alias/fallback for
`MOTION_ANALYSIS_WS_URL`. Motion now has one unambiguous variable name.

#### `VR_DEFAULT_USER_ID`

Removed because VR sessions now require authentication and use the JWT user's
actual ID. A shared fallback user would weaken ownership and could attach several
real users' sessions to one account.

## CRUD Module changes

- Added `GET /health`.
- Added a production database guard: when `ENVIRONMENT=production`,
  `DATABASE_URL` must be PostgreSQL.
- Added a production guard for `INTERNAL_API_KEY`.
- Updated Docker and Railway configuration to use `$PORT`, a non-root user, and
  `/health`.
- Updated the documented monorepo root and Railway config-file paths.

CRUD remains the only application service that imports SQLAlchemy or receives
`DATABASE_URL`.

## Voice Analysis changes

### Result flow

Voice receives audio and transcripts over private WebSockets. After both inputs
close and analysis finishes, it posts the final result to:

```text
VOICE_ANALYSIS_RESULT_CALLBACK_URL
```

The callback now includes `X-Internal-API-Key`, and failed callbacks are retried
up to three times with short exponential delays.

### Configuration

Added/documented:

- `CENTRALIZED_BACKEND_URL`
- `VOICE_ANALYSIS_RESULT_CALLBACK_URL`
- `INTERNAL_API_KEY`
- `ENVIRONMENT`

In production, the internal key must be a non-default secret of at least 32
characters.

### Voice dependencies removed

Removed from `requirements.txt`:

- `openai-whisper`
- `torch`
- `ffmpeg-python`
- `python-multipart`
- `aiofiles`

Reason: recursive source inspection found no imports or calls to these packages.
The implemented analysis uses `librosa`, NumPy, SciPy, SoundFile, and
Praat-Parselmouth. Keeping Whisper and Torch would create a very large Railway
image and long build/start times without providing any runtime behavior.

`python-dotenv` was added because `app/config.py` imports it but it was missing
from the original requirements.

The container installs `libsndfile1`, required by the SoundFile audio stack.

If Whisper transcription is added to the code later, `openai-whisper`, Torch,
and the system FFmpeg executable must be intentionally restored.

## Motion Analysis changes

### Result flow

Motion continues to receive binary JPEG batches through:

```text
WS /ws/motion-analysis/frames/{session_id}
```

It posts the completed analysis to Central Backend, now including
`X-Internal-API-Key`. Callback failures are retried up to three times.

### Configuration

Centralized configuration now defines:

- `CENTRALIZED_BACKEND_URL`
- `INTERNAL_API_KEY`
- `ENVIRONMENT`
- `MOTION_LIVE_PREVIEW`

Production uses `MOTION_LIVE_PREVIEW=0`; Railway containers should not open GUI
preview windows.

### OpenCV dependency change

Changed:

```text
opencv-python==4.10.0.84
```

to:

```text
opencv-contrib-python==4.11.0.86
```

MediaPipe already requires OpenCV Contrib. Installing both base OpenCV and
OpenCV Contrib places two packages providing the same `cv2` module in one image,
which increases image size and can cause file conflicts. The selected Contrib
version was the compatible version resolved during the dependency/import check.

The Docker image also copies both checked-in MediaPipe `.task` model files.

## Conversational AI changes

### Transcript communication

Previously:

```text
Conversational AI --> Voice Analysis directly
```

Now:

```text
Conversational AI --> Central Backend --> Voice Analysis
```

The service uses `CENTRAL_BACKEND_WS_URL` and the shared
`INTERNAL_API_KEY`. The internal key is sent in the WebSocket handshake header.

### Removed Conversational variables

#### `VOICE_ANALYSIS_WS_URL`

Removed because Conversational AI no longer connects directly to Voice.

#### `VOICE_ANALYSIS_SESSION_ID`

Removed because the active `session_id` already arrives in the WebSocket setup
message from Central Backend. A global environment session ID is incorrect for a
multi-user production service.

### Required provider variables

- `OPENAI_API_KEY`
- `DEEPGRAM_API_KEY`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`

The service validates these before starting a conversation session.

### Conversational dependencies removed

#### `deepgram-sdk`

Removed because `providers/deepgram_stt.py` implements the Deepgram streaming
protocol directly with the `websockets` package. Deepgram functionality was not
removed.

#### `elevenlabs`

Removed because `providers/elevenlabs_tts.py` implements the ElevenLabs streaming
protocol directly with `websockets`. ElevenLabs functionality was not removed.

#### `numpy`

Removed because no Conversational Component source file imports or uses NumPy.
Audio chunks are forwarded as bytes.

#### Explicit `pydantic`

Removed because this component does not import Pydantic directly. FastAPI
installs its compatible Pydantic dependency. If this service later adds Pydantic
models, it can be restored as a direct dependency.

### Dependency version changes

- FastAPI and Uvicorn were pinned to the versions used in the successful import
  validation.
- WebSockets was bounded to `>=13.1,<17` because the code uses its asyncio API.
- OpenAI was bounded to `<3` to avoid an unreviewed future major-version upgrade.
- `python-dotenv` was bounded to `<2` for the same production-stability reason.

These changes make Railway builds reproducible; they do not remove provider
functionality.

## Environment-variable ownership after the change

| Variable | Services | Purpose |
|---|---|---|
| `DATABASE_URL` | CRUD only | Railway PostgreSQL connection |
| `INTERNAL_API_KEY` | All five | Authenticated internal calls/events |
| `SECRET_KEY` | Central only | JWT signing |
| `CRUD_BASE_URL` | Central only | Central to CRUD |
| `VOICE_ANALYSIS_WS_URL` | Central only | Central to Voice |
| `MOTION_ANALYSIS_WS_URL` | Central only | Central to Motion |
| `CONVERSATIONAL_COMPONENT_WS_URL` | Central only | Central to Conversational AI |
| `CENTRALIZED_BACKEND_URL` | Voice and Motion | Worker result callbacks to Central |
| `CENTRAL_BACKEND_WS_URL` | Conversational AI | Transcript events to Central |
| AI provider keys | Conversational AI | OpenAI, Deepgram, ElevenLabs |
| R2 variables | Central only | Private presentation storage |

`INTERNAL_API_KEY` must contain the exact same value in all five services.
`SECRET_KEY` must be different and is used only by Central Backend.

## CORS and public URLs

- Only Central Backend should receive a Railway public domain.
- The Vercel dashboard uses Central's public HTTPS URL.
- VR uses Central's public HTTPS and WSS URLs.
- `CORS_ORIGINS` must contain the exact Vercel production origin without a
  trailing slash.
- Add the VR origin only when VR runs in a browser/WebGL origin. Native Unity
  applications do not use browser CORS.
- CRUD, Voice, Motion, and Conversational AI should not be placed in frontend or
  VR configuration.

## Validation performed

- Central Backend: 34 tests passed.
- CRUD Module: 18 tests passed.
- Conversational AI: 3 tests passed.
- Voice production dependencies installed and `app.main` imported successfully.
- Motion production dependencies installed and `app.main` imported successfully.
- All Python application sources passed syntax compilation.
- All five `railway.toml` files parsed successfully.
- Docker build validation reported no warnings for all five Dockerfiles.
- All five Linux production images built successfully with Python 3.11.
- Temporary containers for CRUD, Central, Voice, Motion, and Conversational AI
  started with Railway-style `PORT=8080`; every `/health` endpoint returned
  `status=ok`.

## Known limitations not hidden by deployment configuration

- Password reset creates database tokens but does not send email. No SMTP/email
  provider implementation exists yet.
- R2 credentials are required for presentation-library storage.
- PPTX conversion requires a Gotenberg 8 service; it is an additional runtime
  dependency, not one of the five Python services.
- Central's active VR session coordination is stored in process memory. Keep it
  at one replica and avoid deploying it during active sessions.
- Worker result retries are not a durable queue. A process crash can still lose
  an unsent analysis result.

## Files containing the deployment details

- `RAILWAY_DEPLOYMENT.md`: exact Railway service settings and variables.
- Each service's `.env.example`: local/example environment values.
- Each service's `README.md`: service-specific deployment notes.
- Each service's `Dockerfile` and `railway.toml`: production build/deploy source
  of truth.
