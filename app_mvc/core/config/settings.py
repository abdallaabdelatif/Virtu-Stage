"""Settings contract for shared application configuration."""


class Settings:
    """Expose typed configuration required by core and feature modules."""

    def load(self) -> None:
        """Load configuration values from environment variables, files, or secrets sources."""
        ...

    def validate(self) -> None:
        """Validate that all required configuration values are present and well-formed."""
        ...
