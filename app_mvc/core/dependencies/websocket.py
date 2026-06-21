"""WebSocket dependency providers and authentication helpers."""


class WebSocketDependencies:
    """Provide shared authentication and session-loading helpers for WebSocket flows."""

    async def get_websocket_user(self) -> object:
        """Resolve the authenticated user for a WebSocket connection attempt."""
        ...

    async def validate_session_access(self) -> object:
        """Validate that the current user may access the requested session before connection acceptance."""
        ...
