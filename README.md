# VirtuStage

**Immersive communication training with AI-powered feedback.**

VirtuStage combines an immersive VR training application with a web-based analytics platform. Built on a microservices architecture, it helps users practice job interviews and public speaking through AI-driven conversations, behavioral feedback, and progress tracking.

## Key Features

- **Job interview simulation:** Practice in a realistic interview room with a virtual interviewer whose AI-driven conversation adapts to your responses.
- **Public speaking simulation:** Present to a virtual audience in a presentation hall, using your own uploaded slides to practice speech delivery and audience engagement.
- **Natural voice interaction:** Communicate through real-time speech transcription, AI-generated dialogue, and synthesized speech.
- **Behavioral feedback:** Review vocal tone, clarity, pacing, confidence estimates, and filler-word usage, alongside posture and movement analysis.
- **Reports and progress:** Access automated session reports and behavioral analysis results, upload presentation materials, and track improvement through a web dashboard.

## Platform

Five connected components support the training experience: the VR application, AI conversational services, voice and motion analysis services, a backend and database layer, and the web dashboard. Together, they manage real-time interaction, user accounts, session data, and performance reporting.

## Technology

| Area | Technologies |
| --- | --- |
| VR experience | Unity 3D, OpenXR for compatibility across supported VR headsets |
| Conversational AI & speech | OpenAI GPT (dialogue), Deepgram (speech-to-text), ElevenLabs (text-to-speech) |
| Voice analysis | Librosa, Praat, rule-based scoring |
| Motion analysis | MediaPipe upper-body pose estimation, headset and controller tracking, rule-based posture and movement analysis |
| Backend & communication | Python, FastAPI, WebSocket |
| Database | PostgreSQL |
| Dashboard | React |

## Purpose

VirtuStage brings realistic practice, interactive dialogue, and performance feedback into one platform, helping learners build communication skills through repeated training without constant instructor support.
