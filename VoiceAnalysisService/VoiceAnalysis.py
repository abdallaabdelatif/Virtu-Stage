import os
import json
import wave
import datetime
import struct
import numpy as np
import librosa
import torchaudio
import torch
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

BASE_DIR = "AudioRecordings"
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2
os.makedirs(BASE_DIR, exist_ok=True) 
os.makedirs("pretrained_models", exist_ok=True)

from speechbrain.inference import EncoderClassifier

_emotion_classifier = None

def get_emotion_classifier():
    global _emotion_classifier
    if _emotion_classifier is None:
        model_path = "pretrained_models/emotion_recognition"
        
        if not os.path.exists(model_path):
            print("Downloading emotion model for the first time only...")
        
        _emotion_classifier = EncoderClassifier.from_hparams(
            source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
            savedir=model_path
        )
    
    return _emotion_classifier

app = FastAPI()

def write_wav(pcm_path, wav_path):
    with open(pcm_path, "rb") as pcm:
        pcm_data = pcm.read()

    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)


def emotion_recognition_speechbrain(wav_path: str):
    classifier = get_emotion_classifier()
    signal, sr = torchaudio.load(wav_path)
    if signal.shape[0] > 1: 
        signal = signal.mean(dim=0, keepdim=True)
    
    if sr != 16000:
        resampler = torchaudio.transforms.Resample(sr, 16000)
        signal = resampler(signal)    

    with torch.no_grad():
        prediction = classifier.classify_batch(signal)

    scores = prediction[1].squeeze().tolist() # These values are probabilities their sum equals 1
    labels = prediction[3]

    emotion_scores = {
        labels[i]: round(float(scores[i]), 3)
        for i in range(len(labels))
    }
    return emotion_scores


def paralinguistic_analysis(wav_path):
    y, sr = librosa.load(wav_path, sr=SAMPLE_RATE)

    pitch = librosa.yin(y, fmin=80, fmax=300)
    energy = np.sum(librosa.feature.rms(y=y))
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    pauses = np.sum(np.abs(y) < 0.01) / len(y)
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    mfcc_var = np.var(mfcc)
    
    # Metric Mapping : each one is normalized to [0,1]
    confidence = min(1.0, energy / 5.0)
    focus = max(0.0, 1.0 - pauses)
    anxiety = min(1.0, np.std(pitch) / 50.0)
    clarity = max(0.0, 1.0 - mfcc_var / 10000)

    return {
        "pitch_std": float(np.std(pitch)),
        "energy": float(energy),
        "speech_rate": float(tempo),
        "pause_ratio": float(pauses),
        "mfcc_var": float(mfcc_var),
        "metrics": {
            "confidence": round(confidence, 2),
            "focus": round(focus, 2),
            "anxiety": round(anxiety, 2),
            "clarity": round(clarity, 2)
        }
    }


@app.websocket("/audio")
async def audio_ws(websocket: WebSocket):
    await websocket.accept()

    session_id = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S") # Generate a unique session ID using timestamp
    # Create dedicated directory for each session's files
    session_dir = os.path.join(BASE_DIR, f"session_{session_id}")
    os.makedirs(session_dir, exist_ok=True)

    pcm_path = os.path.join(session_dir, "audio.pcm")
    wav_path = os.path.join(session_dir, "audio.wav")
    result_path = os.path.join(session_dir, "voice_analysis.json")

    pcm_file = open(pcm_path, "ab")
    print(f"Session started: {session_id}")

    try:
        while True:
            data = await websocket.receive_bytes()
            offset = 0
            timestamp_ms = struct.unpack_from("<q", data, offset)[0]
            offset += 8
            pcm_len = struct.unpack_from("<I", data, offset)[0]
            offset += 4
            pcm = data[offset:offset + pcm_len]
            print(f"received {len(pcm)} bytes")
            pcm_file.write(pcm)

    except WebSocketDisconnect:
            print("websocket disconnected")

    
    finally:
        pcm_file.close()
        try:
            await websocket.close()
        except:
            pass
        write_wav(pcm_path, wav_path)
        
        emotions = emotion_recognition_speechbrain(wav_path)
        paraling = paralinguistic_analysis(wav_path)

        output = {
            "session_id": session_id,
            "emotions": emotions,
            "paralinguistic": paraling
        }

        with open(result_path, "w") as f:
            json.dump(output, f, indent=2)

        print(f"Voice Analysis results saved in: {result_path}")
