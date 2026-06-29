# VirtuStage Motion Analysis Service

Rule-based upper-body motion analysis for presentation coaching. Tracks pose (MediaPipe Pose) and hands (MediaPipe Hand Landmarker), evaluates MIT CommLab–aligned rules, and posts numeric scores to the platform database via **central-backend** → **CRUD-Module**.

## Input: WebSocket frame streams (production)

**The service does not read a webcam or video file in production.** Frames arrive over WebSocket as JPEG batches from the VR client, proxied through central-backend.

| Stage | Endpoint | Payload |
|-------|----------|---------|
| VR → central-backend | `WS /ws/vr/frames/{session_id}` | Binary JPEG batches |
| central-backend → this service | `WS /ws/motion-analysis/frames/{session_id}` | Same batches forwarded |
| This service → central-backend | `POST /motion-analyses` (on socket close) | CRUD-shaped JSON scores |

Entry point: `uvicorn app.main:app` or `python -m app.main` — see `app/websocket/frame_session.py`.

Live OpenCV preview is **off by default**. Pass `--preview` when starting the service to show the same overlay as the video demo while frames stream in. Final scores are still POSTed when the WebSocket closes.

`run_webcam_demo.py` is a **local dev tool** (offline video file). It always shows the preview window.

## Architecture

```
VR client
  │  JPEG frame batches (binary)
  ▼
central-backend  :9000   POST /sessions
  │  /ws/vr/frames/{session_id}
  ▼
Motion-Analysis-Service  :9001   WS /ws/motion-analysis/frames/{session_id}
  │  analyze on disconnect
  ▼
central-backend          POST /motion-analyses
  ▼
CRUD-Module              POST /motion-analysis  →  PostgreSQL `motion_analysis`
```

Voice analysis follows the same pattern on port **8001** with audio instead of frames.

## Setup

```powershell
cd Virtu-Stage\Motion-Analysis-Service
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Download models into `models/`:

| File | URL |
|------|-----|
| `pose_landmarker_lite.task` | [pose_landmarker_lite](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task) |
| `hand_landmarker.task` | [hand_landmarker](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task) |

Copy `.env.example` to `.env` and set `CENTRALIZED_BACKEND_URL` (default `http://localhost:9000`).

## Run the service (production)

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 9001
```

With live preview (dev only — OpenCV window on this machine):

```powershell
python -m app.main --preview --host 0.0.0.0 --port 9001
```

Alternatively set `MOTION_LIVE_PREVIEW=1` in `.env` when using `uvicorn app.main:app`.

The service buffers WebSocket frames, runs full analysis on disconnect, and POSTs results to central-backend.

With the full stack running:

1. **CRUD-Module** on port 8000  
2. **central-backend** on port 9000 (`MOTION_ANALYSIS_WS_URL=ws://localhost:9001`)  
3. **Motion-Analysis-Service** on port 9001  
4. VR calls `POST /sessions` then streams frames to `/ws/vr/frames/{session_id}`

Set `VR_DEFAULT_USER_ID` in central-backend `.env` to a valid CRUD user UUID so training sessions are created for the FK on `motion_analysis`.

## Local demo (offline video)

Same live preview as the VR WebSocket path:

```powershell
python run_webcam_demo.py --video "path\to\video.mp4"
```

Press **Q** in the preview window to hide the overlay. Results save to `output/motion_analysis_<id>.json`.

### Test WebSocket preview without VR

```powershell
# Terminal 1 — with preview
python -m app.main --preview --port 9001

# Terminal 2 — sends a video as fake VR batches
python test_ws_frame_client.py --video "path\to\video.mp4"
```

Through central-backend:

```powershell
python test_ws_frame_client.py --video "path\to\video.mp4" --via-central-backend
```

## Core modules

| Module | Role |
|--------|------|
| `app/models/motion_frame_data.py` | Pose + optional `HandTrack` per frame |
| `app/models/motion_rule_engine.py` | Rule thresholds and per-frame evaluations |
| `app/models/motion_analysis_service.py` | Frame + session orchestration |
| `app/models/motion_analysis_result.py` | `to_crud_payload()` for database fields |
| `app/models/presentation_ratings.py` | Categorical assessment (excellent → needs_work) |
| `app/analysis/frame_processor.py` | JPEG → landmarks (pose + hands) |
| `app/analysis/motion_pipeline.py` | Session analysis pipeline |
| `app/frame/vr_batch.py` | VR binary batch decoder |
| `app/websocket/frame_handler.py` | **Production entry** — WebSocket frame ingest |

## Rules tracked

Posture (forward/backward lean, shoulders, crossed arms), gaze proxy (looking down), gestures (hand speed, stillness, dominance), composure (hand-near-face via palm/fingertips, fidgeting), stability (head movement, rocking, sudden jerks).

## Database payload

`MotionAnalysisResult.to_crud_payload()` maps to CRUD `MotionAnalysisCreate`:

- `head_stability_score`, `head_movement_variance`, `head_angle`, `head_avg_velocity`
- `fidgeting_level`, `fidgeting_score`, `sudden_index`, `repetitive_index`
- `hand_movement_score`, `left_hand_avg_velocity`, `right_hand_avg_velocity`
- `posture_quality`, `posture_score`, `nervousness_indicator`, `motion_overall_score`

Categorical ratings and recommendations are stored in CRUD as `presentation_assessment` (JSON), plus `recommendations`, `dominant_posture_type`, and `session_metrics`. Numeric scores remain in the existing columns.

## VR frame batch format

Little-endian binary (from `FrameWebSocketStreamer`):

```
UInt32 frame_count
repeat frame_count times:
  UInt32 index
  Int64  timestamp_ms
  UInt32 jpg_length
  byte[jpg_length] JPEG data
```

## Ports (local defaults)

| Service | Port |
|---------|------|
| CRUD-Module | 8000 |
| Voice-Analysis-Service | 8001 |
| Motion-Analysis-Service | 9001 |
| central-backend | 9000 |

## Railway production

Deploy as private service `motion-analysis` with root
`/backend/Motion-Analysis-Service`, config
`/backend/Motion-Analysis-Service/railway.toml`, and healthcheck `/health`.
Production uses Railway `$PORT`, `MOTION_LIVE_PREVIEW=0`, a private
`CENTRALIZED_BACKEND_URL`, and the shared `INTERNAL_API_KEY`. The MediaPipe model
files in `models/` are copied into the image. See
[`../RAILWAY_DEPLOYMENT.md`](../RAILWAY_DEPLOYMENT.md).
