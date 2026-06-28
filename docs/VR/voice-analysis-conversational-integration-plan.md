# Voice Analysis ↔ Conversational Service Integration Plan

## Goal
Wire the conversational service to the voice-analysis transcript websocket so every recognized transcript is forwarded to the voice-analysis service and buffered there for later analysis.

## Current State
- The voice-analysis service already exposes a transcript websocket endpoint in [Voice-Analysis-Service/app/websocket/transcript_handler.py](../Voice-Analysis-Service/app/websocket/transcript_handler.py).
- The transcript handler expects JSON payloads shaped like:
  - `{"type": "transcript", "text": "..."}`
- The conversational service in [ConversationalComponent/main.py](../ConversationalComponent/main.py) already receives STT transcripts and drives the LLM/TTS flow, but it does not currently forward those transcripts to the voice-analysis socket.

## Proposed Implementation Plan

### 1. Add configuration for the voice-analysis websocket
In [ConversationalComponent/config/settings.py](../ConversationalComponent/config/settings.py), add environment-driven settings such as:
- `VOICE_ANALYSIS_WS_URL` defaulting to `ws://localhost:8001`
- `VOICE_ANALYSIS_TRANSCRIPT_PATH` defaulting to `/ws/voice-analysis/transcript/{session_id}`
- `CONVERSATIONAL_WS_PORT` defaulting to `8002` for the conversational websocket endpoint

### 2. Reuse or create a session identifier
The conversation should be associated with the same session id used by the VR flow.
- Prefer reusing the session id already available in the VR flow from [VR/BackendClient.cs.txt](../VR/BackendClient.cs.txt) and [VR/FrameWebsocketStreamer.cs.txt](../VR/FrameWebsocketStreamer.cs.txt).
- If the conversational websocket is opened directly without a session id, generate one locally and send it in the first initialization message to the client.

### 3. Open an outbound websocket from the conversational service
Inside [ConversationalComponent/main.py](../ConversationalComponent/main.py):
- After the Unity websocket is accepted and the session context is known, open a client websocket to the voice-analysis transcript endpoint.
- The target URL should be:
  - `ws://localhost:8001/ws/voice-analysis/transcript/{session_id}`
- Once the websocket is connected, forward each final transcript from the STT loop as:
  - `{"type": "transcript", "text": "<transcript text>"}`

### 4. Keep the voice-analysis service behavior intact
No major changes should be required in [Voice-Analysis-Service/app/websocket/transcript_handler.py](../Voice-Analysis-Service/app/websocket/transcript_handler.py) because it already accepts transcript fragments and appends them to the buffer.
- The existing `session_id` from the URL is enough to group fragments.
- The conversational service only needs to send the expected JSON shape.

### 5. Close the transcript websocket cleanly
When the conversational session ends or the Unity websocket disconnects:
- close the outbound voice-analysis transcript websocket gracefully
- ensure the voice-analysis service receives the disconnect and continues its analysis flow

## Message Contract
The conversational service should send this JSON payload to the voice-analysis transcript websocket:

```json
{
  "type": "transcript",
  "text": "the real transcribed user speech"
}
```

The `session_id` is already part of the websocket path, so it does not need to be repeated in the message body.

## Porting / Configuration Notes
- Local service ports:
  - `5432` → PostgreSQL
  - `5173` → Frontend
  - `8000` → CRUD Module
  - `8001` → Voice-Analysis-Service
  - `8002` → ConversationalComponent (`/ws`)
  - `9000` → Central Backend
  - `9001` → Motion-Analysis-Service
- The direct conversational → voice-analysis transcript websocket should use port `8001` because that is the voice-analysis service endpoint.
- If a temporary local bridge or proxy is introduced later for debugging, use `9100` as a new unused port.

## Validation Steps
1. Start the voice-analysis service on port `8001`.
2. Start the conversational component on port `8002`.
3. Connect the Unity/VR client to the conversational websocket.
4. Send audio/transcript content through the conversational path.
5. Confirm that the voice-analysis transcript websocket receives the fragments and that the buffer grows for the same `session_id`.
