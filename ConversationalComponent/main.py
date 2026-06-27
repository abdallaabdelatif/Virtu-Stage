import asyncio
import json
import os

from fastapi import FastAPI
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from websockets.client import connect as ws_connect

from config.settings import settings

from providers.deepgram_stt import DeepgramSTT
from providers.openai_llm import OpenAILLM
from providers.elevenlabs_tts import ElevenLabsTTS

from pipeline.voice_session import VoiceSession
from pipeline.conversation_pipeline import ConversationPipeline
from voice_analysis_bridge import build_transcript_ws_url, create_transcript_payload, resolve_session_id

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()
    print("Unity connected")

    mode = 1
    job = ""
    session_id = None
    mode_message = await websocket.receive_text()
    mode_data = json.loads(mode_message)

    if mode_data.get("type") == "set_mode":
        mode = mode_data.get("mode", 1)
    if mode == 1:
        job_message = await websocket.receive_text()
        job_data = json.loads(job_message)
        if job_data.get("type") == "set_job":
            job = job_data.get("job", "")
        print(f"Job selected: {job}")

    session_data = json.loads(await websocket.receive_text())
    if session_data.get("type") == "set_session":
        session_id = session_data.get("sessionId")

    if not session_id:
        raise RuntimeError("Missing session_id from client")

    print(f"Mode selected: {mode}")

    if mode == 1:
        prompt = (
            f"You are holding an interview with the user "
            f"who is applying for the role of {job}. "
            f"Ask about their education and past work experience. "
            f"If the user says anything unrelated to the "
            f"{job} interview ask the user to stick to the topic."
        )
    else:
        prompt = ""

    session = VoiceSession(mode,prompt)

    stt = DeepgramSTT(settings.DEEPGRAM_API_KEY)

    llm = OpenAILLM(settings.OPENAI_API_KEY)

    tts = ElevenLabsTTS(settings.ELEVENLABS_API_KEY,settings.ELEVENLABS_VOICE_ID)

    pipeline = ConversationPipeline(llm,tts)

    transcript_ws = None
    transcript_ws_url = build_transcript_ws_url(settings.VOICE_ANALYSIS_WS_URL, session_id)
    try:
        transcript_ws = await ws_connect(transcript_ws_url)
        print(f"Voice analysis transcript websocket connected: {transcript_ws_url}")
    except Exception as exc:  # pragma: no cover - defensive runtime path
        print(f"Could not connect to voice analysis transcript websocket: {exc}")

    await stt.connect()

    async def send_tts(text: str):
        await websocket.send_text(
            json.dumps(
                {
                    "type": "tts_start"
                }
            )
        )

        async for chunk in tts.stream_audio(text):
            await websocket.send_bytes(chunk)

        await websocket.send_text(
            json.dumps(
                {
                    "type": "tts_end"
                }
            )
        )

    async def generate_presentation_question():
        if len(session.presentation_transcripts) == 0:
            return

        presentation_text = "\n".join(session.presentation_transcripts)

        prompt = f"""
The following is a presentation given by the user.

Presentation:

{presentation_text}

Generate one realistic question that an examiner might ask.
Only output the question.
"""

        question = await llm.generate_response([{"role": "user","content": prompt}])

        print("Generated Question:", question)

        await send_tts(question)

    async def unity_listener():
        while True:
            message = await websocket.receive()
            if message.get("bytes") is not None:
                audio_chunk = message["bytes"]
                await stt.send_audio(audio_chunk)

            elif message.get("text") is not None:
                data = json.loads(message["text"])
                msg_type = data.get("type")
                if (session.mode == 2 and msg_type == "generate_question"):
                    await generate_presentation_question()

    async def stt_processing():
        while True:
            transcript = (await stt.receive_transcript())

            if not transcript:
                continue

            print("User:",transcript)
            if transcript_ws is not None:
                try:
                    await transcript_ws.send(create_transcript_payload(transcript))
                except Exception as exc:  # pragma: no cover - defensive runtime path
                    print(f"Failed to forward transcript to voice analysis: {exc}")

            if session.mode == 1:
                response = (
                    await pipeline.process_transcript(session,transcript)
                )
                print("Assistant:",response)
                await send_tts(response)

            else:
                session.presentation_transcripts.append(transcript)
                print("Stored presentation transcript")

    try:
        await asyncio.gather(unity_listener(),stt_processing())

    except WebSocketDisconnect:

        print("Unity disconnected")

    finally:
        if transcript_ws is not None:
            await transcript_ws.close()
        await stt.close()