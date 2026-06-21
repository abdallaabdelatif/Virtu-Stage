"""Shared declarative base and metadata registration helpers."""


class BaseModel:
    """Represent the shared ORM base class used by repositories and feature models."""

    @classmethod
    def table_name(cls) -> str:
        """Return the database table name associated with the model class."""
        ...
