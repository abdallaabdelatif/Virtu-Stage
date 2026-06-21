"""Shared request and response schema contracts."""


class BaseResponse:
    """Represent the common response contract returned by REST endpoints."""


class AuthenticatedUser:
    """Represent the minimum shared user identity required across features."""


class PaginationRequest:
    """Represent shared pagination input used by list-oriented endpoints."""


class PaginationResponse:
    """Represent shared pagination metadata returned by list-oriented endpoints."""
