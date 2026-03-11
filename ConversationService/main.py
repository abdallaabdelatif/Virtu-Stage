from fastapi import FastAPI, WebSocket
from services.deepgram import DeepgramClient
from services.openai import OpenAIClient
from services.elevenlabs import ElevenLabsClient

app = FastAPI()
stt = DeepgramClient()
openai = OpenAIClient()
tts = ElevenLabsClient()


@app.websocket("/conversation")
async def conversation_socket(ws: WebSocket):
    await ws.accept()

    conversation_history = []

    try:
        while True:
            # Receive audio chunk from unity
            audio_chunk = await ws.receive_bytes()
            # Send audio to deepgram
            transcript = await stt.transcribe(audio_chunk)
            if not transcript:
                continue
            # Add user message to conversation history
            conversation_history.append({
                "role": "player",
                "content": transcript
            })
            # Send transcript to GPT
            response_text = await openai.generate_reply(
                conversation_history
            )
            # add gpt response to conversation history
            conversation_history.append({
                "role": "interviewer",
                "content": response_text
            })
            # Convert response to speech
            audio_response = await tts.generate_speech(response_text)
            # Send audio back to unity
            await ws.send_bytes(audio_response)

    except Exception as e:
        print("Connection closed:", e)