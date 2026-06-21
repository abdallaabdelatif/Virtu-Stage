"""Shared authorization-rule contracts."""


class AuthorizationRules:
    """Centralize reusable authorization and ownership checks."""

    def ensure_resource_owner(self, resource_owner_id: int, current_user_id: int) -> None:
        """Ensure that the current user owns the requested resource."""
        ...

    def ensure_session_is_active(self, session_status: str) -> None:
        """Ensure that a session remains active before allowing new work on it."""
        ...
