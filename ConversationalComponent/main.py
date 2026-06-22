import asyncio
import json

from fastapi import FastAPI
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from config.settings import settings

from providers.deepgram_stt import DeepgramSTT
from providers.openai_llm import OpenAILLM
from providers.elevenlabs_tts import ElevenLabsTTS

from pipeline.voice_session import VoiceSession
from pipeline.conversation_pipeline import ConversationPipeline

app = FastAPI()

SYSTEM_PROMPT = """
You are conducting an interview with the user.
Ask about education and previous experience.
Keep the discussion focused on the interview.
"""


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    print("Unity connected")

    session = VoiceSession(SYSTEM_PROMPT)

    stt = DeepgramSTT(settings.DEEPGRAM_API_KEY)

    llm = OpenAILLM(settings.OPENAI_API_KEY)

    tts = ElevenLabsTTS(
        settings.ELEVENLABS_API_KEY,
        settings.ELEVENLABS_VOICE_ID
    )

    pipeline = ConversationPipeline(llm,tts)

    await stt.connect()

    async def unity_to_stt():
        while True:
            audio_chunk = (await websocket.receive_bytes())
            await stt.send_audio(audio_chunk)

    async def stt_to_tts():
        while True:
            transcript = (
                await stt.receive_transcript()
            )

            if not transcript:
                continue

            print("User:",transcript)

            response = (
                await pipeline.process_transcript(session,transcript)
            )

            print("Assistant:",response)

            await websocket.send_text(
                json.dumps(
                    {
                        "type": "tts_start"
                    }
                )
            )

            async for chunk in tts.stream_audio(response):
                await websocket.send_bytes(chunk)

            await websocket.send_text(
                json.dumps(
                    {
                        "type": "tts_end"
                    }
                )
            )

    try:

        await asyncio.gather(unity_to_stt(),stt_to_tts())

    except WebSocketDisconnect:

        print("Unity disconnected")

    finally:

        await stt.close()