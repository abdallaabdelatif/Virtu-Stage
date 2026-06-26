"""Stream a local video to the motion-analysis WebSocket as VR-style JPEG batches."""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

import cv2
import httpx
import websockets

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.frame.vr_batch import VRFrame, encode_vr_frame_batch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream a video over the frame WebSocket.")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--session-id", type=str, default="")
    parser.add_argument("--url", type=str, default="")
    parser.add_argument("--motion-host", type=str, default="ws://localhost:9001")
    parser.add_argument("--central-backend", type=str, default="http://localhost:9000")
    parser.add_argument("--via-central-backend", action="store_true")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--jpg-quality", type=int, default=70)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--batch-delay", type=float, default=0.5)
    return parser.parse_args()


def _read_video_frames(video_path: Path, *, jpg_quality: int, max_frames: int) -> tuple[list[VRFrame], float]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 120:
        fps = 30.0
    frames: list[VRFrame] = []
    index = 0
    timestamp_ms = 0
    step_ms = int(1000 / fps)
    while cap.isOpened():
        ret, bgr = cap.read()
        if not ret:
            break
        ok, encoded = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality])
        if not ok:
            continue
        frames.append(VRFrame(index=index, timestamp_ms=timestamp_ms, jpeg=encoded.tobytes()))
        index += 1
        timestamp_ms += step_ms
        if max_frames > 0 and index >= max_frames:
            break
    cap.release()
    if not frames:
        raise RuntimeError("No frames read from video")
    return frames, fps


async def _ensure_cb_session(central_backend: str, session_id: str) -> None:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{central_backend.rstrip('/')}/sessions",
            json={"session_id": session_id, "mode": 2, "job": "ws-preview-test"},
            timeout=10.0,
        )
        if r.status_code not in (201, 409):
            r.raise_for_status()


def _resolve_ws_url(args: argparse.Namespace, session_id: str) -> str:
    if args.url:
        return args.url
    if args.via_central_backend:
        base = args.central_backend.replace("http://", "ws://").replace("https://", "wss://")
        return f"{base.rstrip('/')}/ws/vr/frames/{session_id}"
    return f"{args.motion_host.rstrip('/')}/ws/motion-analysis/frames/{session_id}"


async def _stream(args: argparse.Namespace) -> None:
    session_id = args.session_id or str(uuid.uuid4())
    vr_frames, fps = _read_video_frames(
        args.video.resolve(), jpg_quality=args.jpg_quality, max_frames=args.max_frames
    )
    if args.via_central_backend:
        await _ensure_cb_session(args.central_backend, session_id)
    ws_url = _resolve_ws_url(args, session_id)
    print(f"Session ID : {session_id}\nFrames     : {len(vr_frames)}\nWebSocket  : {ws_url}\n")
    async with websockets.connect(ws_url, max_size=None) as ws:
        batch: list[VRFrame] = []
        for frame in vr_frames:
            batch.append(frame)
            if len(batch) < args.batch_size:
                continue
            await ws.send(encode_vr_frame_batch(batch))
            batch.clear()
            if args.batch_delay > 0:
                await asyncio.sleep(args.batch_delay)
        if batch:
            await ws.send(encode_vr_frame_batch(batch))
    print("Done — check the motion service preview window on the server machine.")


def main() -> None:
    asyncio.run(_stream(parse_args()))


if __name__ == "__main__":
    main()
