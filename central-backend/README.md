## Local setup

```powershell
docker compose up -d gotenberg
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9000
```

Gotenberg runs on `localhost:3001` for local development. PDF files are rendered
directly with PyMuPDF; PPTX files are first converted to PDF by Gotenberg and are
then rendered by the same PDF pipeline.

Presentation-specific central-backend variables:

```env
GOTENBERG_URL=http://localhost:3001
GOTENBERG_TIMEOUT_SECONDS=120
PRESENTATION_MAX_SLIDES=100
PRESENTATION_IMAGE_WIDTH=1920
R2_SIGNED_URL_EXPIRES_SECONDS=3600
R2_AVATAR_BUCKET_NAME=virtustage
PUBLIC_API_URL=http://localhost:9000
AVATAR_MAX_BYTES=1048576
AVATAR_SIZE=512
```

The R2 bucket stays private. `GET /api/files` returns metadata only. Call
`GET /api/files/{file_id}/slides` after a user selects a presentation to receive
ordered, short-lived URLs for the generated PNG files.

Avatars are normalized to square WebP images and stored under the `avatars/`
prefix. By default they use the same private R2 bucket and are served through
the public, opaque `/api/avatars/{user_id}/{avatar_id}.webp` endpoint. Set
`R2_AVATAR_BUCKET_NAME` to isolate them in another bucket. If that bucket has a
public custom domain, set `AVATAR_PUBLIC_BASE_URL` to use the CDN URL directly.
Never make the presentation bucket public.

## Railway deployment

Deploy this folder as the central backend service:

```text
Railway service: central-backend
Root Directory: /backend/central-backend
Railway Config File: /backend/central-backend/railway.toml
```

Required service variables:

```env
CRUD_BASE_URL=http://<crud-private-domain>:<crud-port>
INTERNAL_API_KEY=<same-secret-used-by-crud-service>
SECRET_KEY=<long-random-secret>
FRONTEND_URL=https://virtu-stage-dashboard.vercel.app
CORS_ORIGINS=https://virtu-stage-dashboard.vercel.app
ENVIRONMENT=production
PUBLIC_API_URL=https://<central-backend-public-domain>
GOTENBERG_URL=http://gotenberg:3000
```

This service does not connect directly to PostgreSQL and does not need `DATABASE_URL`.
The frontend should call this central backend URL, not the CRUD service URL.
Voice, Motion, and Conversational AI URLs should use their Railway private
domains. See [`../RAILWAY_DEPLOYMENT.md`](../RAILWAY_DEPLOYMENT.md) for exact
service names, config paths, variable references, CORS, and networking.
