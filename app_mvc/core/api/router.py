"""Root API routing definitions for the feature-based application."""


class ApiRouter:
    """Compose feature routers into the final REST and WebSocket routing tree."""

    def include_feature_routes(self) -> None:
        """Register all feature REST routes into the root API router."""
        ...

    def include_websocket_routes(self) -> None:
        """Register all feature WebSocket routes into the root application router."""
        ...

    def build(self) -> object:
        """Return the assembled router object used by the application entrypoint."""
        ...
