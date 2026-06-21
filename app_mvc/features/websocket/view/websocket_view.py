"""WebSocket view definitions for session-scoped real-time communication."""


class WebSocketView:
    """Accept and manage session-scoped WebSocket connections, delegating work to feature controllers."""

    async def connect(self, session_id: int, connection: object) -> None:
        """Authenticate the connection and initialize the real-time session context."""
        ...

    async def receive_message(self, session_id: int, message: object) -> object:
        """Route an inbound WebSocket message to the appropriate controller workflow."""
        ...

    async def disconnect(self, session_id: int, connection: object) -> None:
        """Handle connection cleanup and any required session shutdown work."""
        ...
