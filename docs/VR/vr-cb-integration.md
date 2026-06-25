## VR → Central Backend Integration Plan

**TL;DR**

Implement a Central Backend VR integration layer that receives VR audio/video streams, forwards raw audio in parallel to both the Voice Analysis Service and the Conversational AI service, and returns ElevenLabs TTS audio back to VR while persisting analysis results to CRUD. Video analysis should be supported as a future parallel path.

---

## Phase 1 — Central Backend VR session and ingestion

1. Create `central-backend/app/api/vr.py` with:
   - `POST /sessions`
     - Create or reserve `session_id`
     - Accept session metadata: `mode`, `job`, `user_id`
     - Return `{ "session_id": "..." }`
   - `WebSocket /ws/vr/audio/{session_id}`
     - Receive VR raw PCM audio chunks
     - Accept initial control messages: `set_mode`, `set_job`, `audio_start`, `audio_end`
     - Maintain session state and downstream proxy sockets
   - `WebSocket /ws/vr/frames/{session_id}`
     - Receive VR frame batch payloads
     - Validate batch header, frame count, and `session_id`
     - Buffer or forward frames for future video analysis

2. Add schema models to `central-backend/app/api/schemas/vr.py`:
   - `VRSessionCreate`
   - `VRAudioControlMessage`
   - `VRFrameBatch`
   - `VoiceAnalysisResultPayload`
   - `ConversationalTTSMessage`

3. Extend `central-backend/app/config.py` with:
   - `VOICE_ANALYSIS_WS_URL`
   - `CONVERSATIONAL_COMPONENT_WS_URL`
   - `VIDEO_ANALYSIS_WS_URL`
   - `CRUD_BASE_URL`
   - `CENTRALIZED_BACKEND_URL`
   - keep existing auth config values

4. Add downstream proxy clients:
   - `central-backend/app/clients/voice_analysis_proxy.py`
     - open websocket to `VOICE_ANALYSIS_WS_URL` at `/ws/voice-analysis/audio/{session_id}`
     - forward binary audio chunks to voice analysis
   - `central-backend/app/clients/conversational_proxy.py`
     - open websocket to `CONVERSATIONAL_COMPONENT_WS_URL` at `/ws`
     - send `set_mode` and `set_job`
     - forward VR audio bytes
     - receive ElevenLabs TTS bytes and relay them back to VR
   - optional `central-backend/app/clients/video_analysis_proxy.py`
     - placeholder for future video analysis websocket or HTTP integration

5. Update `central-backend/app/main.py`:
   - include `app.api.vr` router
   - preserve auth middleware for protected endpoints
   - allow websocket upgrade on `/ws/vr/*`
   - add startup/shutdown cleanup if needed for active session proxies

6. Update `central-backend/requirements.txt`:
   - add `websockets==13.1`
   - keep `httpx`, `fastapi`, `python-jose`, `pydantic`, `python-dotenv`

---

## Phase 2 — VR client integration

1. Update `VR/BackendClient.cs.txt`:
   - change `wsUrl` to CB audio endpoint, e.g. `ws://<cb-host>:<port>/ws/vr/audio/{session_id}`
   - add session handshake before streaming:
     - request `session_id` via `POST /sessions`
     - or send `{"type":"set_mode",...}` and `{"type":"set_job",...}` as initial websocket messages
   - continue streaming `MicCapture.AudioQueue` PCM bytes unchanged
   - send a clean `audio_end` or close the socket on session end
   - keep receiving bytes from CB for TTS playback and JSON control events

2. Update `VR/FrameWebsocketStreamer.cs.txt`:
   - change `wsUrl` to CB frame endpoint, e.g. `ws://<cb-host>:<port>/ws/vr/frames/{session_id}`
   - send session metadata before each batch if endpoint does not encode it
   - keep existing batch serialization but add a minimal frame header if needed

3. Adjust `VR/MicCapture.cs.txt` if required:
   - track audio streaming start/stop boundaries
   - optionally enqueue a final marker so CB can close conversational and analysis flows cleanly

4. Keep `VR/StreamingAudioPlayer.cs.txt` as-is:
   - it already accepts backend TTS audio bytes
   - ensure the CB returns audio data in the same byte-message form

---

## Phase 3 — Parallel audio routing in Central Backend

1. When VR connects to `/ws/vr/audio/{session_id}`:
   - create a session context object
   - open two downstream websocket sessions:
     - voice analysis proxy to `VOICE_ANALYSIS_WS_URL` + `/ws/voice-analysis/audio/{session_id}`
     - conversational proxy to `CONVERSATIONAL_COMPONENT_WS_URL` + `/ws`
   - forward all VR binary audio chunks to both downstream sockets in parallel

2. Conversational proxy behavior:
   - send initial JSON messages to ConversationalComponent:
     - `{"type":"set_mode","mode":...}`
     - `{"type":"set_job","job":"..."}`
   - forward each VR audio chunk as websocket bytes
   - receive websocket text messages from ConversationalComponent:
     - `tts_start` -> forward to VR
     - `tts_end` -> forward to VR
   - receive websocket binary audio chunks from ConversationalComponent and forward them to VR
   - close the conversational websocket when VR disconnects or session ends

3. Voice analysis proxy behavior:
   - forward VR audio chunks to voice analysis service
   - close downstream socket when VR disconnects so analysis begins
   - do not expect voice analysis to return audio over this socket

4. On VR disconnect:
   - close both downstream sockets gracefully
   - mark session complete for voice analysis and conversational processing

---

## Phase 4 — Voice analysis result ingestion and persistence

1. Add `POST /voice-analyses` to `central-backend/app/api/vr.py` or a dedicated internal router
   - validate the body against `VoiceAnalysisCreate` or a custom schema
   - optionally attach `session_id`, `received_at`, and source metadata
   - forward the payload to CRUD via `crud_client.create_voice_analysis(payload)`
   - return `201` on success

2. Update `central-backend/app/clients/crud_client.py`:
   - add `async def create_voice_analysis(self, payload: dict[str, Any]) -> dict[str, Any]`
   - post to `{CRUD_BASE_URL}/voice-analysis`

3. Add retries and fallback logic:
   - transient CRUD failures should be retried or queued for later replay
   - persist failed payloads locally if necessary
   - return structured errors on permanent failure

4. Add a placeholder route for video analysis results:
   - `POST /video-analyses` or `POST /internal/analysis/video`
   - validate video analysis payload shape
   - forward to CRUD if video schema exists, or keep as a buffer for future implementation

---

## Phase 5 — Conversational AI details and service contract

1. ConversationalComponent workflow is already built around:
   - `DeepgramSTT` for streaming speech-to-text
   - `OpenAILLM` for response generation
   - `ElevenLabsTTS` for streaming TTS audio

2. CB should preserve this flow:
   - VR audio -> CB -> ConversationalComponent websocket
   - ConversationalComponent -> Deepgram -> OpenAI -> ElevenLabs
   - ElevenLabs audio chunks -> CB -> VR

3. Required CB-to-ConversationalComponent contract:
   - text control messages: `set_mode`, `set_job`, `generate_question`
   - raw bytes forwarded exactly as `VR/BackendClient.cs.txt` currently produces
   - binary audio return messages forwarded unchanged

4. Required env vars for the conversational path:
   - `CONVERSATIONAL_COMPONENT_WS_URL`
   - `OPENAI_API_KEY`
   - `DEEPGRAM_API_KEY`
   - `ELEVENLABS_API_KEY`
   - `ELEVENLABS_VOICE_ID`

---

## Phase 6 — VR <-> CB <-> Conversational AI end-to-end handling

1. On each VR audio chunk:
   - send to voice analysis service
   - send to conversational component service
2. Speech analysis and conversation must occur in parallel:
   - voice analysis provides post-session metrics
   - conversational AI provides live dialogue and TTS playback
3. End-of-session flow:
   - VR disconnect closes downstream sockets
   - voice analysis completes and posts results to CB
   - conversational component ends the TTS session and stops sending audio

---

## Phase 7 — Testing, documentation, and future video support

1. Add tests for:
   - CB websocket session lifecycle
   - parallel forwarding to both voice analysis and conversational proxies
   - TTS relay back to VR
   - CRUD persistence of voice analysis results
   - failure and retry behavior

2. Add docs for VR integration:
   - session creation
   - `/ws/vr/audio/{session_id}` flow
   - `/ws/vr/frames/{session_id}` frame upload contract
   - conversational control messages
   - required env vars

3. Future-proof video analysis:
   - keep the `/ws/vr/frames/{session_id}` endpoint
   - add a video-analysis proxy client later
   - mirror the audio parallel-loading pattern for video analysis

---

## Implementation checklist

- [ ] `central-backend/app/api/vr.py`
- [ ] `central-backend/app/api/schemas/vr.py`
- [ ] `central-backend/app/clients/voice_analysis_proxy.py`
- [ ] `central-backend/app/clients/conversational_proxy.py`
- [ ] `central-backend/app/clients/crud_client.py` update
- [ ] `central-backend/app/config.py` update
- [ ] `central-backend/app/main.py` router inclusion
- [ ] `central-backend/requirements.txt` update
- [ ] `VR/BackendClient.cs.txt` session handshake + audio routing
- [ ] `VR/FrameWebsocketStreamer.cs.txt` CB frame endpoint
- [ ] `docs/vr-cb-integration.md` final plan

---

## Current discovered state

- `central-backend` currently supports auth and a protected route only; no VR/websocket ingestion exists yet
- `VR/BackendClient.cs.txt` sends raw PCM audio to a generic backend websocket at `/ws`
- `Voice-Analysis-Service` already supports `/ws/voice-analysis/audio/{session_id}` and posts results to CB at `/voice-analyses`
- `ConversationalComponent` already supports Deepgram->OpenAI->ElevenLabs via `/ws`
- CRUD already exposes `/voice-analysis` for persistence
