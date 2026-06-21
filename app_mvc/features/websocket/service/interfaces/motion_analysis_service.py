"""Abstract motion-analysis contract used by the motion controller."""

from abc import ABC, abstractmethod


class MotionAnalysisService(ABC):
    """Define motion-analysis behavior independently from the concrete provider."""

    @abstractmethod
    async def analyze(self, motion_data: object) -> object:
        """Return a motion-analysis result for the supplied motion payload."""
        ...
