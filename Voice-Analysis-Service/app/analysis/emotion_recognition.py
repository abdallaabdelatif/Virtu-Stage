# Branch 1: Speech Emotion Recognition
# wav2vec model + SpeechBrain classfier


from __future__ import annotations
import logging
from dataclasses import dataclass
import torchaudio
import torch
from speechbrain.inference.interfaces import foreign_class

logger = logging.getLogger(__name__)

MODEL_LABEL_ORDER = ("neutral", "angry", "happy", "sad")


@dataclass(frozen=True)
class EmotionScores:
    neutral: float
    happy: float
    sad: float
    angry: float

    @property
    def dominant_emotion(self) -> str:
        scores = {
            "neutral": self.neutral,
            "happy": self.happy,
            "sad": self.sad,
            "angry": self.angry,
        }
        return max(scores, key=scores.get)


class EmotionRecognizer:
    def __init__(self) -> None:
        logger.info("Loading wav2vec2 emotion recognition model.")
        try:
            self._classifier = foreign_class(
                source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
                pymodule_file="custom_interface.py",
                classname="CustomEncoderWav2vec2Classifier",
            )
            logger.info("Emotion recognition model loaded.")
        except Exception:
            logger.exception("Failed to load emotion recognition model.")
            raise

    def predict(self, wav_path: str) -> EmotionScores:
        waveform, sr = torchaudio.load(wav_path)
        if sr != 16000:
            waveform = torchaudio.functional.resample(waveform, sr, 16000)
        out_prob, _, _, text_lab = self._classifier.classify_batch(waveform)
        probs = torch.exp(out_prob).squeeze(0).tolist()
        label_map = {"ang": "angry", "hap": "happy", "neu": "neutral", "sad": "sad"}
        score_by_label = {}
        for lab, prob in zip(text_lab, probs):
            full_emotion = label_map.get(lab.lower(), lab.lower())
            score_by_label[full_emotion] = prob
        return EmotionScores(
            neutral=score_by_label.get("neutral", 0.0),
            happy=score_by_label.get("happy", 0.0),
            sad=score_by_label.get("sad", 0.0),
            angry=score_by_label.get("angry", 0.0),
        )
