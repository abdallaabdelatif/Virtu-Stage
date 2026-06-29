# Railway production deployment

Deploy all services in one Railway project and environment. Only `central-backend`
gets a public domain. CRUD, Voice, Motion, Conversational AI, PostgreSQL, and
Gotenberg should use Railway private networking.

Railway config files are authoritative. Leave Build Command and Start Command
empty in the Railway UI; the Dockerfiles and `railway.toml` files provide them.
Railway config-file paths are repository-absolute, even when a Root Directory is
set.

## Services

| Railway service | Root Directory | Railway Config File | Exposure | Health |
|---|---|---|---|---|
| `crud-module` | `/backend/CRUD-Module` | `/backend/CRUD-Module/railway.toml` | Private | `/health` |
| `central-backend` | `/backend/central-backend` | `/backend/central-backend/railway.toml` | Public + private | `/health` |
| `voice-analysis` | `/backend/Voice-Analysis-Service` | `/backend/Voice-Analysis-Service/railway.toml` | Private | `/health` |
| `motion-analysis` | `/backend/Motion-Analysis-Service` | `/backend/Motion-Analysis-Service/railway.toml` | Private | `/health` |
| `conversational-ai` | `/backend/ConversationalComponent` | `/backend/ConversationalComponent/railway.toml` | Private | `/health` |

| Service | Entrypoint | Production process | Protocols | Data dependency |
|---|---|---|---|---|
| CRUD | `app.main:app` | `uvicorn app.main:app` | HTTP | Railway PostgreSQL |
| Central | `app.main:app` | `uvicorn app.main:app` | HTTP + WebSocket | CRUD only |
| Voice | `app.main:app` | `uvicorn app.main:app` | HTTP + WebSocket | Central callback only |
| Motion | `app.main:app` | `uvicorn app.main:app` | HTTP + WebSocket | Central callback only |
| Conversational AI | `main:app` | `uvicorn main:app` | HTTP + WebSocket | Central events + AI providers |

The exact Python package sets are pinned or bounded in each service's
`requirements.txt`; Docker installs those files directly under Python 3.11.

Set `PORT=8080` on each Python service. The application does not embed this
number; every Dockerfile reads `$PORT`. An explicit Railway service variable is
needed so another service can reference `${{service.PORT}}` when constructing a
private-network URL.

## Shared secret

Generate one high-entropy `INTERNAL_API_KEY` (at least 32 characters), add it as
a Railway shared variable, and share it with all five Python services. Seal it in
Railway. It authenticates Central -> CRUD requests and worker -> Central events.

Generate a separate high-entropy `SECRET_KEY` for Central Backend JWT signing.
Never reuse `INTERNAL_API_KEY`, provider keys, or database credentials as the JWT
secret.

## Variables

### `crud-module`

```env
PORT=8080
ENVIRONMENT=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
INTERNAL_API_KEY=${{shared.INTERNAL_API_KEY}}
```

`DATABASE_URL` is required and must be PostgreSQL in production. This is the only
application service that receives database credentials.

### `central-backend`

```env
PORT=8080
ENVIRONMENT=production
CRUD_BASE_URL=http://${{crud-module.RAILWAY_PRIVATE_DOMAIN}}:${{crud-module.PORT}}
VOICE_ANALYSIS_WS_URL=ws://${{voice-analysis.RAILWAY_PRIVATE_DOMAIN}}:${{voice-analysis.PORT}}
MOTION_ANALYSIS_WS_URL=ws://${{motion-analysis.RAILWAY_PRIVATE_DOMAIN}}:${{motion-analysis.PORT}}
CONVERSATIONAL_COMPONENT_WS_URL=ws://${{conversational-ai.RAILWAY_PRIVATE_DOMAIN}}:${{conversational-ai.PORT}}/ws
INTERNAL_API_KEY=${{shared.INTERNAL_API_KEY}}
SECRET_KEY=<unique-random-JWT-secret-at-least-32-characters>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
ANALYSIS_TIMEOUT_SECONDS=600
FRONTEND_URL=https://virtu-stage-dashboard.vercel.app
CORS_ORIGINS=https://virtu-stage-dashboard.vercel.app
PASSWORD_RESET_EXPIRE_MINUTES=15
R2_ACCOUNT_ID=<required-for-library-files>
R2_ACCESS_KEY_ID=<required-for-library-files>
R2_SECRET_ACCESS_KEY=<required-for-library-files>
R2_BUCKET_NAME=<required-for-library-files>
R2_SIGNED_URL_EXPIRES_SECONDS=3600
GOTENBERG_URL=http://${{gotenberg.RAILWAY_PRIVATE_DOMAIN}}:${{gotenberg.PORT}}
GOTENBERG_TIMEOUT_SECONDS=120
PRESENTATION_MAX_SLIDES=100
PRESENTATION_IMAGE_WIDTH=1920
```

Use the exact Vercel production origin with no trailing slash. Add an explicit VR
WebGL/browser origin to the comma-separated `CORS_ORIGINS` value if applicable.
Native Unity clients do not use browser CORS. Do not put a private Railway URL in
the Vercel dashboard or VR client; both use Central Backend's public HTTPS/WSS
domain only.

R2 is needed for presentation-library uploads. PPTX conversion additionally
needs a private Gotenberg 8 service. PDF rendering is handled in Central Backend.

### `voice-analysis`

```env
PORT=8080
ENVIRONMENT=production
CENTRALIZED_BACKEND_URL=http://${{central-backend.RAILWAY_PRIVATE_DOMAIN}}:${{central-backend.PORT}}
VOICE_ANALYSIS_RESULT_CALLBACK_URL=http://${{central-backend.RAILWAY_PRIVATE_DOMAIN}}:${{central-backend.PORT}}/voice-analyses
INTERNAL_API_KEY=${{shared.INTERNAL_API_KEY}}
```

### `motion-analysis`

```env
PORT=8080
ENVIRONMENT=production
CENTRALIZED_BACKEND_URL=http://${{central-backend.RAILWAY_PRIVATE_DOMAIN}}:${{central-backend.PORT}}
INTERNAL_API_KEY=${{shared.INTERNAL_API_KEY}}
MOTION_LIVE_PREVIEW=0
```

### `conversational-ai`

```env
PORT=8080
ENVIRONMENT=production
CENTRAL_BACKEND_WS_URL=ws://${{central-backend.RAILWAY_PRIVATE_DOMAIN}}:${{central-backend.PORT}}
INTERNAL_API_KEY=${{shared.INTERNAL_API_KEY}}
OPENAI_API_KEY=<secret>
DEEPGRAM_API_KEY=<secret>
ELEVENLABS_API_KEY=<secret>
ELEVENLABS_VOICE_ID=<provider-voice-id>
```

Seal all provider keys and R2 credentials. No SMTP/email provider integration is
implemented: production password-reset requests create a token but do not send
email. Add an email provider before treating password reset as production-ready.

## Runtime flow and URLs

- Dashboard and VR use `https://<central-domain>` for HTTP and
  `wss://<central-domain>/ws/vr/...` for streams.
- Central calls CRUD at `CRUD_BASE_URL` and forwards audio, frames, and
  conversation traffic to the three private worker WebSockets.
- Conversational AI sends transcript events to Central's authenticated internal
  WebSocket; Central relays them to Voice Analysis.
- Voice posts to `/voice-analyses`; Motion posts to `/motion-analyses`; both use
  the shared internal API key. Central then writes through CRUD.
- No frontend or VR configuration should contain CRUD or worker URLs.

## Railway UI checklist

1. Create PostgreSQL and the five named services in one project/environment.
2. Add Gotenberg 8 if PPTX library uploads are required.
3. Set each Root Directory and repository-absolute Railway Config File above.
4. Clear UI Build Command, Start Command, healthcheck, and restart overrides.
5. Set variables, including explicit `PORT`, and deploy private dependencies
   before Central Backend.
6. Generate a public domain only for `central-backend`.
7. Point Vercel's existing `VITE_API_URL` and the VR HTTP/WS base URLs at that
   Central domain. This repository does not change the deployed dashboard.

Keep Central Backend at one replica. Active VR/WebSocket coordination is stored
in process memory; horizontal replicas require shared session state and sticky
routing, which are not implemented.

## Release blockers and known limits

- The password-reset flow stores reset tokens but has no email/SMTP provider, so
  users will not receive production reset links until mail delivery is added.
- Presentation-library uploads require configured Cloudflare R2 credentials;
  PPTX conversion additionally requires a reachable Gotenberg 8 service.
- Voice and Motion retry Central callbacks three times, but there is no durable
  message queue. A worker crash after analysis can still lose an unsent result.
- Active VR sessions are in Central Backend memory. Deploy one replica and avoid
  redeploying Central during live sessions.
