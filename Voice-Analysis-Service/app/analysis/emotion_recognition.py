# Branch 1: Speech Emotion Recognition
# wav2vec model + SpeechBrain classfier


from __future__ import annotations
import logging
from dataclasses import dataclass
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
        self._classifier = foreign_class(
            source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
            pymodule_file="custom_interface.py",
            classname="CustomEncoderWav2vec2Classifier",
        )
        logger.info("Emotion recognition model loaded.")

    def predict(self, wav_path: str) -> EmotionScores:
        _, probabilities, _, _ = self._classifier.classify_file(wav_path)
        probs = torch.exp(probabilities).squeeze(0).tolist()
        score_by_label = dict(zip(MODEL_LABEL_ORDER, probs))
        return EmotionScores(
            neutral=score_by_label["neutral"],
            happy=score_by_label["happy"],
            sad=score_by_label["sad"],
            angry=score_by_label["angry"],
        )
