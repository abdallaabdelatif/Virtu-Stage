# Voice Analysis Service

FastAPI entrypoint: `app.main:app`. It exposes HTTP health/session-analysis routes
and audio/transcript WebSockets. Central Backend sends audio; transcript events
arrive through Central Backend; final results are posted to Central Backend.

Production command is defined by the Dockerfile and reads Railway `$PORT`.
Deploy as private service `voice-analysis` with root
`/backend/Voice-Analysis-Service`, config
`/backend/Voice-Analysis-Service/railway.toml`, and healthcheck `/health`.

Required production variables are `PORT`, `ENVIRONMENT=production`,
`CENTRALIZED_BACKEND_URL`, `VOICE_ANALYSIS_RESULT_CALLBACK_URL`, and the shared
`INTERNAL_API_KEY`. See [`../RAILWAY_DEPLOYMENT.md`](../RAILWAY_DEPLOYMENT.md).
