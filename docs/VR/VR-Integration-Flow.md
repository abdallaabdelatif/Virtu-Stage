# VR Integration End-to-End Flow

## Overview
This document outlines the complete flow from VR client connection through session lifecycle, including audio/video streaming, voice analysis, conversational AI, and session persistence.

## Current implementation status
The following pieces are now implemented in the workspace:
- The conversational service opens an outbound websocket to the voice-analysis transcript endpoint and forwards each recognized transcript.
- The voice-analysis service accepts those transcript fragments and buffers them for the matching session ID.
- The direct bridge currently targets the voice-analysis service on port 8001 using the endpoint `/ws/voice-analysis/transcript/{session_id}`.
- The central backend already exposes the frame websocket endpoint and forwards frames to the motion-analysis service.
- The motion-analysis service processes inbound JPEG batches and posts its result back to the central backend for CRUD persistence.
- The conversational websocket runs on port 8002, and the motion-analysis service runs on port 9001.

### Current runtime configuration
- `VOICE_ANALYSIS_WS_URL` → defaults to `ws://localhost:8001`
- `VOICE_ANALYSIS_SESSION_ID` → optional session override; otherwise a fallback session name is used
- `MOTION_ANALYSIS_WS_URL` → defaults to `ws://localhost:9001`
- `CENTRALIZED_BACKEND_URL` → used by the motion-analysis service to post results back to the central backend
- `CRUD_BASE_URL` → used by the central backend to forward analysis results to CRUD
- `VR_DEFAULT_USER_ID` → should point to a valid CRUD user ID so training sessions can be created for motion/voice analysis results
- Existing service ports remain:
  - `5432` → PostgreSQL
  - `5173` → Frontend
  - `8000` → CRUD Module
  - `8001` → Voice-Analysis-Service
  - `8002` → ConversationalComponent (`/ws`)
  - `9000` → Central Backend
  - `9001` → Motion-Analysis-Service

---

## Phase 1: Session Initialization

### Step 1.1: VR Client Creates Session
- **File:** `VR/BackendClient.cs.txt`
- **Method:** `CreateSession()`
- **Action:** Generates unique session ID, sends session metadata (mode, job) to backend

### Step 1.2: Backend Session Creation
- **File:** `central-backend/app/api/vr.py`
- **Endpoint:** `POST /sessions`
- **Action:** Validates session data, stores session in session_store, returns session ID to VR client

---

## Phase 2: WebSocket Connection & Proxy Initialization

### Step 2.1: VR Client Connects to Audio WebSocket
- **File:** `VR/BackendClient.cs.txt`
- **Method:** `OnOpen()` (BackendClient Unity callback)
- **Action:** Connects to `ws://backend:9000/ws/vr/audio/{session_id}`

### Step 2.2: Backend Creates Dual-Proxy Setup
- **File:** `central-backend/app/api/vr.py`
- **Handler:** `vr_audio_socket()` WebSocket endpoint
- **Action:** 
  - Creates `VoiceAnalysisProxy` connection to Voice-Analysis-Service
  - Creates `ConversationalProxy` connection to ConversationalComponent
  - Spawns async task `forward_conv_to_vr()` for bidirectional relay

### Step 2.3: Downstream Service Connections
- **VoiceAnalysisProxy File:** `central-backend/app/clients/voice_analysis_proxy.py`
  - **Method:** `connect()`
  - **Action:** Establishes WebSocket to Voice-Analysis-Service at the configured audio endpoint

- **ConversationalProxy File:** `central-backend/app/clients/conversational_proxy.py`
  - **Method:** `connect()`
  - **Action:** Establishes WebSocket to ConversationalComponent, sends initialization (`set_mode`, `set_job`)

- **Implemented direct bridge:** `ConversationalComponent/main.py`
  - **Action:** Opens a direct websocket to `ws://localhost:8001/ws/voice-analysis/transcript/{session_id}`
  - **Payload:** Sends each recognized transcript as `{"type": "transcript", "text": "..."}`
  - **Effect:** The voice-analysis service buffers the transcript fragments for later analysis

### Step 2.4: VR Frame Streamer Connects
- **File:** `VR/FrameWebsocketStreamer.cs.txt`
- **Method:** `InitializeWebsocket()`
- **Action:** Waits for session ID, connects to `ws://backend:9000/ws/vr/frames/{session_id}`

### Step 2.5: Backend Opens Motion Analysis Proxy
- **File:** `central-backend/app/api/vr.py`
- **Handler:** `vr_frame_socket()`
- **Action:** Creates a `MotionAnalysisProxy` and opens a websocket to the motion-analysis service at `/ws/motion-analysis/frames/{session_id}`

---

## Phase 3: Parallel Audio/Video Streaming

### Step 3.1: VR Client Sends Raw Audio
- **File:** `VR/BackendClient.cs.txt`
- **Method:** `SendAudioLoop()`
- **Action:** Continuously sends audio frames to backend via WebSocket

### Step 3.2: Backend Receives Audio
- **File:** `central-backend/app/api/vr.py`
- **Handler:** `vr_audio_socket()` 
- **Action:** Receives raw audio bytes from VR client

### Step 3.3: Audio Parallel Forwarding
Backend forwards audio to both services simultaneously:

- **To Voice-Analysis-Service:**
  - **File:** `central-backend/app/clients/voice_analysis_proxy.py`
  - **Method:** `send_bytes()`
  - **Action:** Forwards audio chunk to Voice-Analysis-Service

- **To ConversationalComponent:**
  - **File:** `central-backend/app/clients/conversational_proxy.py`
  - **Method:** `send_bytes()`
  - **Action:** Forwards audio chunk to Conversational AI service

### Step 3.4: VR Client Sends Frame Data
- **File:** `VR/FrameWebsocketStreamer.cs.txt`
- **Method:** `CaptureAndStreamFrames()`
- **Action:** Captures camera frames, batches them, sends to backend

### Step 3.5: Backend Receives Frame Data
- **File:** `central-backend/app/api/vr.py`
- **Handler:** `vr_frame_socket()` WebSocket endpoint
- **Action:** Receives frame batches from VR and forwards them to the motion-analysis service

### Step 3.6: Motion-Analysis-Service Processes Frame Batches
- **File:** `Motion-Analysis-Service/app/websocket/frame_handler.py`
- **Handler:** `frame_socket()`
- **Action:** Buffers inbound JPEG batches, runs the analysis pipeline on disconnect, and posts the result back to the central backend

---

## Phase 4: Motion Analysis Processing and Persistence

### Step 4.1: Motion-Analysis-Service Receives VR Batches
- **File:** `Motion-Analysis-Service/app/websocket/frame_handler.py`
- **Handler:** `frame_socket()`
- **Action:** Accepts binary frame batches from the central backend and stores them in `FrameBuffer`

### Step 4.2: Motion Analysis Pipeline Runs
- **File:** `Motion-Analysis-Service/app/analysis/motion_pipeline.py`
- **Action:** Processes pose/hand landmarks to compute posture, gesture, stability, and composure scores

### Step 4.3: Result Is Posted Back to Central Backend
- **File:** `Motion-Analysis-Service/app/websocket/result_sender.py`
- **Action:** Converts the analysis result into a CRUD-compatible payload and posts it to `POST /motion-analyses` on the central backend

### Step 4.4: Central Backend Persists to CRUD
- **File:** `central-backend/app/api/vr.py`
- **Handler:** `ingest_motion_analysis()`
- **Action:** Forwards the analysis payload to CRUD via `crud_client.create_motion_analysis()`

### Step 4.5: CRUD Stores the Motion Analysis Record
- **File:** `central-backend/app/clients/crud_client.py`
- **Method:** `create_motion_analysis()`
- **Action:** POSTs the payload to the CRUD module at `/motion-analysis`

---

## Phase 5: Voice Analysis Processing

### Step 5.1: Voice-Analysis-Service Processes Audio
- **File:** `Voice-Analysis-Service/app/main.py`
- **Handler:** WebSocket audio endpoint
- **Services:**
  - `Voice-Analysis-Service/app/analysis/emotion_recognition.py` - Emotion detection
  - `Voice-Analysis-Service/app/analysis/paralinguistic.py` - Speech patterns
  - `Voice-Analysis-Service/app/analysis/pause_analysis.py` - Silence/pause detection
  - `Voice-Analysis-Service/app/analysis/transcript_metrics.py` - Text metrics
- **Action:** Processes cumulative audio, generates analysis results

### Step 5.2: Backend Receives Voice Analysis Results
- **File:** `central-backend/app/clients/voice_analysis_proxy.py`
- **Method:** `receive_message()`
- **Action:** Receives analysis results as WebSocket messages

### Step 5.3: Voice Analysis Persisted to CRUD
- **File:** `central-backend/app/api/vr.py`
- **Handler:** `POST /voice-analyses`
- **Action:** Receives analysis results from frontend, forwards to CRUD service

- **File:** `central-backend/app/clients/crud_client.py`
- **Method:** `create_voice_analysis()`
- **Action:** HTTP POST to CRUD service at `/voice-analysis` endpoint

- **File:** `CRUD-Module/app/routers/voice_analysis.py`
- **Handler:** Stores voice analysis in database via model `CRUD-Module/app/models/voice_analysis.py`

---

## Phase 6: Conversational AI Processing & Relay

### Step 6.1: ConversationalComponent Processes Input
- **File:** `ConversationalComponent/main.py`
- **Pipeline:** `ConversationalComponent/pipeline/conversation_pipeline.py`
- **Action:** 
  - Receives audio/text from backend or direct websocket input
  - Generates conversational response
  - Produces TTS audio output and control messages
  - Forwards each recognized transcript to the voice-analysis transcript websocket for buffering and later analysis

### Step 6.2: Backend Receives Conversational Response
- **File:** `central-backend/app/clients/conversational_proxy.py`
- **Method:** `receive_message()`
- **Action:** Receives TTS audio or text/control messages from ConversationalComponent

### Step 6.3: Backend Relays to VR Client
- **File:** `central-backend/app/api/vr.py`
- **Task:** `forward_conv_to_vr()` async function
- **Action:** Continuously receives from ConversationalProxy and sends to VR client via WebSocket

### Step 6.4: VR Client Handles Response
- **File:** `VR/BackendClient.cs.txt`
- **Handler:** WebSocket message handler
- **Action:**
  - If TTS audio: passes to `StreamingAudioPlayer` for playback
  - If control message: updates UI/game state accordingly

---

## Phase 7: Session End & Cleanup

### Step 7.1: VR Client Initiates End
- **File:** `VR/BackendClient.cs.txt`
- **Method:** `OnDestroy()` or manual disconnect
- **Action:** Sends `audio_end` control message to signal session completion

### Step 7.2: Backend Detects Session End
- **File:** `central-backend/app/api/vr.py`
- **Handler:** `vr_audio_socket()` message handler
- **Action:** 
  - Detects `audio_end` control message type
  - Closes `VoiceAnalysisProxy` connection

### Step 7.3: Voice-Analysis Final Processing
- **File:** `Voice-Analysis-Service/app/main.py`
- **Action:** WebSocket close triggers final analysis computation and result generation

### Step 7.4: Session Cleanup
- **File:** `central-backend/app/api/vr.py`
- **Handler:** `vr_audio_socket()` finally block
- **Action:**
  - Removes session from `session_store`
  - Closes all proxy connections
  - Releases resources

---

## Data Flow Diagram Summary

```
┌─────────────────┐
│   VR Client     │
│   (Unity C#)    │
└────────┬────────┘
         │
    ┌────┴─────────────────────────────┐
    │                                  │
    │ 1. POST /sessions                │ 2. WS /ws/vr/audio/{id}
    │    (session init)                │    (audio stream)
    │                                  │
    ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Central Backend (FastAPI)                       │
│  - Session Management (session_store)                        │
│  - Dual-Proxy Forwarding                                     │
│  - WebSocket Relay (voice → conversational)                  │
└──────┬──────────────────────┬──────────────────────┬────────┘
       │                      │                      │
       │ VoiceAnalysisProxy   │ ConversationalProxy  │ Frame Handler
       │                      │                      │
       ▼                      ▼                      ▼
┌───────────────────┐  ┌──────────────────┐    ┌──────────────┐
│ Voice-Analysis-   │  │ Conversational    │    │ Frame Buffer │
│ Service           │  │ Component (AI)    │    │ (Storage)    │
│ - Emotion         │  │ - LLM Processing  │    │              │
│ - Paralinguistic  │  │ - TTS Generation  │    │              │
│ - Pause Analysis  │  │ - Response Gen    │    │              │
└─────────┬─────────┘  └────────┬──────────┘    └──────────────┘
          │                     │
          └─────────┬───────────┘
                    │
                    ▼ (Results)
          ┌─────────────────────┐
          │   CRUD Module       │
          │ - Persistence Layer │
          │ - Database Storage  │
          └─────────────────────┘
```

---

## Key Control Messages

| Message Type | Source | Target | Purpose |
|---|---|---|---|
| `set_mode` | Backend | ConversationalComponent | Initialize interaction mode |
| `set_job` | Backend | ConversationalComponent | Set job/task context |
| `generate_question` | VR Client | Conversational (via Backend) | Request AI response |
| `audio_end` | VR Client | Backend | Signal session completion |
| `tts_start` / `tts_end` | ConversationalComponent | VR Client (via Backend) | Audio playback markers |

---

## Files Involved by Category
### Motion Analysis Service
- `Motion-Analysis-Service/app/main.py` - FastAPI entry point
- `Motion-Analysis-Service/app/websocket/frame_handler.py` - Production websocket ingress
- `Motion-Analysis-Service/app/websocket/result_sender.py` - Result posting to central backend
- `Motion-Analysis-Service/app/analysis/motion_pipeline.py` - Pose/hand analysis pipeline
- `Motion-Analysis-Service/app/models/motion_analysis_result.py` - Result model and CRUD payload mapping
### VR Client (Unity C#)
- `VR/BackendClient.cs.txt` - Main session & audio client
- `VR/FrameWebsocketStreamer.cs.txt` - Frame capture & streaming
- `VR/StreamingAudioPlayer.cs.txt` - TTS audio playback
- `VR/MicCapture.cs.txt` - Microphone input capture

### Central Backend (FastAPI)
- `central-backend/app/api/vr.py` - VR session & WebSocket handlers
- `central-backend/app/clients/voice_analysis_proxy.py` - Voice service proxy
- `central-backend/app/clients/conversational_proxy.py` - Conversational service proxy
- `central-backend/app/clients/crud_client.py` - CRUD persistence client
- `central-backend/app/api/schemas/vr.py` - Data validation models

### Voice Analysis Service
- `Voice-Analysis-Service/app/main.py` - WebSocket entry point
- `Voice-Analysis-Service/app/analysis/pipeline.py` - Analysis orchestration
- `Voice-Analysis-Service/app/analysis/emotion_recognition.py` - Emotion detection
- `Voice-Analysis-Service/app/analysis/paralinguistic.py` - Speech analysis
- `Voice-Analysis-Service/app/analysis/pause_analysis.py` - Silence detection
- `Voice-Analysis-Service/app/analysis/transcript_metrics.py` - Text metrics

### Conversational AI
- `ConversationalComponent/main.py` - WebSocket entry point
- `ConversationalComponent/pipeline/conversation_pipeline.py` - AI processing
- `ConversationalComponent/providers/openai_llm.py` - LLM interface
- `ConversationalComponent/providers/elevenlabs_tts.py` - TTS interface

### CRUD Module (Persistence)
- `CRUD-Module/app/main.py` - API server
- `CRUD-Module/app/routers/voice_analysis.py` - Voice analysis storage
- `CRUD-Module/app/models/voice_analysis.py` - Data model
- `CRUD-Module/app/database.py` - Database connection

---

## Session Lifecycle States

1. **INITIALIZED** → Session created, proxies established
2. **STREAMING** → Audio/frames flowing to services
3. **PROCESSING** → Services analyzing audio and generating responses
4. **RESPONDING** → Conversational output relayed back to VR
5. **COMPLETED** → Session ended, resources cleaned up
6. **PERSISTED** → Analysis results stored in CRUD database
