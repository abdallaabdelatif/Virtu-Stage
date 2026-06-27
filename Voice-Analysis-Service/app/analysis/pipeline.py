# Runs two independent analysis pipelines: audio & transcript

from __future__ import annotations
import logging
from pathlib import Path
import librosa
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.analysis.emotion_recognition import EmotionRecognizer
from app.analysis.paralinguistic import ParalinguisticAnalyzer
from app.analysis.pause_analysis import PauseAnalyzer
from app.analysis.transcript_metrics import TranscriptAnalyzer
from app.audio.audio_buffer import SAMPLE_RATE_HZ, AudioBuffer
from app.audio.transcript_buffer import TranscriptBuffer
from app.schemas.result import (
    AudioAnalysisResult,
    EmotionScoresSchema,
    ParalinguisticScoresSchema,
    PauseAnalysisSchema,
    TranscriptAnalysisResult,
)

logger = logging.getLogger(__name__)


class AudioAnalysisPipeline:
    def __init__(self) -> None:
        self.emotion_recognizer = EmotionRecognizer()
        self.paralinguistic_analyzer = ParalinguisticAnalyzer()
        self.pause_analyzer = PauseAnalyzer()
        self.executor = ThreadPoolExecutor(max_workers=3)

    async def run(
        self, session_id: str, audio_buffer: AudioBuffer
    ) -> AudioAnalysisResult:
        if not audio_buffer.has_audio:
            raise ValueError(f"No audio accumulated for session {session_id}")

        wav_bytes = audio_buffer.to_wav_bytes()
        wav_path = self.write_temp_wav(wav_bytes)

        try:
            audio, sample_rate = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: librosa.load(wav_path, sr=SAMPLE_RATE_HZ, mono=True),
            )
            duration_seconds = len(audio) / sample_rate

            logger.info(
                "Running audio-based analysis branch in parallel for session %s",
                session_id,
            )

            # def emotion_job():
            #     logger.info("Emotion started")
            #     result = self.emotion_recognizer.predict(wav_path)
            #     logger.info("Emotion finished")
            #     return result

            # def para_job():
            #     logger.info("Paralinguistic started")
            #     result = self.paralinguistic_analyzer.analyze(audio, sample_rate)
            #     logger.info("Paralinguistic finished")
            #     return result

            # def pause_job():
            #     logger.info("Pause analysis started")
            #     result = self.pause_analyzer.analyze(audio, sample_rate)
            #     logger.info("Pause analysis finished")
            #     return result

            # emotion_scores, paralinguistic_scores, pause_result = await asyncio.gather(
            #     asyncio.get_event_loop().run_in_executor(self.executor, emotion_job),
            #     asyncio.get_event_loop().run_in_executor(self.executor, para_job),
            #     asyncio.get_event_loop().run_in_executor(self.executor, pause_job),
            # )
            # logger.info("Gather completed")
            emotion_scores, paralinguistic_scores, pause_result = await asyncio.gather(
                asyncio.get_event_loop().run_in_executor(
                    self.executor, lambda: self.emotion_recognizer.predict(wav_path)
                ),
                asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: self.paralinguistic_analyzer.analyze(audio, sample_rate),
                ),
                asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: self.pause_analyzer.analyze(audio, sample_rate),
                ),
            )
            logger.info("Building AudioAnalysisResult")
            result = AudioAnalysisResult(
                emotions=EmotionScoresSchema(
                    neutral=emotion_scores.neutral,
                    happy=emotion_scores.happy,
                    sad=emotion_scores.sad,
                    angry=emotion_scores.angry,
                    dominant=emotion_scores.dominant_emotion,
                ),
                paralinguistic=ParalinguisticScoresSchema(
                    anxiety_level=paralinguistic_scores.anxiety_level,
                    confidence_score=paralinguistic_scores.confidence_score,
                    clarity_level=paralinguistic_scores.clarity_level,
                    focus_score=paralinguistic_scores.focus_score,
                ),
                pauses=PauseAnalysisSchema(
                    pause_ratio=pause_result.pause_ratio,
                    pause_count=pause_result.pause_count,
                    longest_pause_seconds=pause_result.longest_pause_seconds,
                ),
                duration_seconds=duration_seconds,
            )
            logger.info("Returning AudioAnalysisResult")
            return result
        finally:
            Path(wav_path).unlink(missing_ok=True)

    @staticmethod
    def write_temp_wav(wav_bytes: bytes) -> str:
        tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_file.write(wav_bytes)
        tmp_file.close()
        return tmp_file.name

    def __del__(self):
        executor = getattr(self, "executor", None)
        if executor:
            executor.shutdown(wait=False)


class TranscriptAnalysisPipeline:
    def __init__(self) -> None:
        self.transcript_analyzer = TranscriptAnalyzer()

    def run(
        self,
        session_id: str,
        transcript_buffer: TranscriptBuffer,
        duration_seconds: float,
    ) -> TranscriptAnalysisResult:
        if not transcript_buffer.has_text:
            raise ValueError(f"No transcript accumulated for session {session_id}")

        logger.info("Running transcript metrics for session %s", session_id)
        metrics = self.transcript_analyzer.analyze(
            transcript_buffer.full_transcript(), duration_seconds
        )

        return TranscriptAnalysisResult(
            filler_word_count=metrics.filler_word_count,
            speech_rate_wpm=metrics.speech_rate_wpm,
        )
