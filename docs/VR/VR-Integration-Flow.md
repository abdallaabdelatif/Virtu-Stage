# VR Integration End-to-End Flow

## Overview
This document outlines the complete flow from VR client connection through session lifecycle, including audio/video streaming, voice analysis, conversational AI, and session persistence.

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
- **Action:** Connects to `ws://backend:8082/ws/vr/audio/{session_id}`

### Step 2.2: Backend Creates Dual-Proxy Setup
- **File:** `central-backend/app/api/vr.py`
- **Handler:** `vr_audio_socket()` WebSocket endpoint
- **Action:** 
  - Creates `VoiceAnalysisProxy` connection to Voice-Analysis-Service
  - Creates `ConversationalProxy` connection to ConversationalComponent
  - Spawns async task `forward_conv_to_vr()` for bidirectional relay

### Step 2.3: Proxies Connect to Downstream Services
- **VoiceAnalysisProxy File:** `central-backend/app/clients/voice_analysis_proxy.py`
  - **Method:** `connect()`
  - **Action:** Establishes WebSocket to Voice-Analysis-Service at configured endpoint

- **ConversationalProxy File:** `central-backend/app/clients/conversational_proxy.py`
  - **Method:** `connect()`
  - **Action:** Establishes WebSocket to ConversationalComponent, sends initialization (set_mode, set_job)

### Step 2.4: VR Frame Streamer Connects
- **File:** `VR/FrameWebsocketStreamer.cs.txt`
- **Method:** `InitializeWebSocket()`
- **Action:** Waits for session ID, connects to `ws://backend:8082/ws/vr/frames/{session_id}`

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
- **Handler:** `vr_frames_socket()` WebSocket endpoint
- **Action:** Receives and stores frame batch data

---

## Phase 4: Voice Analysis Processing

### Step 4.1: Voice-Analysis-Service Processes Audio
- **File:** `Voice-Analysis-Service/app/main.py`
- **Handler:** WebSocket audio endpoint
- **Services:**
  - `Voice-Analysis-Service/app/analysis/emotion_recognition.py` - Emotion detection
  - `Voice-Analysis-Service/app/analysis/paralinguistic.py` - Speech patterns
  - `Voice-Analysis-Service/app/analysis/pause_analysis.py` - Silence/pause detection
  - `Voice-Analysis-Service/app/analysis/transcript_metrics.py` - Text metrics
- **Action:** Processes cumulative audio, generates analysis results

### Step 4.2: Backend Receives Voice Analysis Results
- **File:** `central-backend/app/clients/voice_analysis_proxy.py`
- **Method:** `receive_message()`
- **Action:** Receives analysis results as WebSocket messages

### Step 4.3: Voice Analysis Persisted to CRUD
- **File:** `central-backend/app/api/vr.py`
- **Handler:** `POST /voice-analyses`
- **Action:** Receives analysis results from frontend, forwards to CRUD service

- **File:** `central-backend/app/clients/crud_client.py`
- **Method:** `create_voice_analysis()`
- **Action:** HTTP POST to CRUD service at `/voice-analysis` endpoint

- **File:** `CRUD-Module/app/routers/voice_analysis.py`
- **Handler:** Stores voice analysis in database via model `CRUD-Module/app/models/voice_analysis.py`

---

## Phase 5: Conversational AI Processing & Relay

### Step 5.1: ConversationalComponent Processes Input
- **File:** `ConversationalComponent/main.py`
- **Pipeline:** `ConversationalComponent/pipeline/conversation_pipeline.py`
- **Action:** 
  - Receives audio/text from backend
  - Generates conversational response
  - Produces TTS audio output and control messages

### Step 5.2: Backend Receives Conversational Response
- **File:** `central-backend/app/clients/conversational_proxy.py`
- **Method:** `receive_message()`
- **Action:** Receives TTS audio or text/control messages from ConversationalComponent

### Step 5.3: Backend Relays to VR Client
- **File:** `central-backend/app/api/vr.py`
- **Task:** `forward_conv_to_vr()` async function
- **Action:** Continuously receives from ConversationalProxy and sends to VR client via WebSocket

### Step 5.4: VR Client Handles Response
- **File:** `VR/BackendClient.cs.txt`
- **Handler:** WebSocket message handler
- **Action:**
  - If TTS audio: passes to `StreamingAudioPlayer` for playback
  - If control message: updates UI/game state accordingly

---

## Phase 6: Session End & Cleanup

### Step 6.1: VR Client Initiates End
- **File:** `VR/BackendClient.cs.txt`
- **Method:** `OnDestroy()` or manual disconnect
- **Action:** Sends `audio_end` control message to signal session completion

### Step 6.2: Backend Detects Session End
- **File:** `central-backend/app/api/vr.py`
- **Handler:** `vr_audio_socket()` message handler
- **Action:** 
  - Detects `audio_end` control message type
  - Closes `VoiceAnalysisProxy` connection

### Step 6.3: Voice-Analysis Final Processing
- **File:** `Voice-Analysis-Service/app/main.py`
- **Action:** WebSocket close triggers final analysis computation and result generation

### Step 6.4: Session Cleanup
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
