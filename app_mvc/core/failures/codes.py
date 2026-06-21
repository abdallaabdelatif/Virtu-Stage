"""Shared error-code definitions for HTTP and WebSocket error reporting."""


class ErrorCodes:
    """Enumerate application-wide failure codes used across features."""

    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    SESSION_ENDED = "SESSION_ENDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
