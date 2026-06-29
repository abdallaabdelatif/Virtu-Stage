# Conversational AI Service

FastAPI entrypoint: `main:app`. It exposes `/health` over HTTP and `/ws` for the
Central Backend conversation proxy. It uses Deepgram STT, OpenAI LLM, and
ElevenLabs TTS APIs. Transcript events go to Central Backend's authenticated
internal WebSocket; this service does not call Voice or CRUD directly.

Deploy as private service `conversational-ai` with root
`/backend/ConversationalComponent`, config
`/backend/ConversationalComponent/railway.toml`, and healthcheck `/health`.
Required variables: `PORT`, `ENVIRONMENT=production`, `CENTRAL_BACKEND_WS_URL`,
the shared `INTERNAL_API_KEY`, `OPENAI_API_KEY`, `DEEPGRAM_API_KEY`,
`ELEVENLABS_API_KEY`, and `ELEVENLABS_VOICE_ID`.

See [`../RAILWAY_DEPLOYMENT.md`](../RAILWAY_DEPLOYMENT.md) for exact Railway
reference-variable values and networking.
