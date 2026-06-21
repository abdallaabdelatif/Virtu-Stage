"""Rule-based provider adapter for motion-analysis workflows."""


class RuleBasedMotionService:
    """Implement the motion-analysis service contract using deterministic rule-based logic."""

    async def analyze(self, motion_data: object) -> object:
        """Return motion-analysis insights derived from the supplied movement payload."""
        ...
