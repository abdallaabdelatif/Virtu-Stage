from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncConnection


MIGRATION_ID = "20260623_core_auth"


def _run_core_auth_migration(sync_connection) -> None:
    dialect = sync_connection.dialect.name
    timestamp_type = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"
    boolean_default = "TRUE" if dialect == "postgresql" else "1"

    sync_connection.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_id VARCHAR(100) PRIMARY KEY,
                applied_at {timestamp_type} NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    already_applied = sync_connection.execute(
        text(
            "SELECT migration_id FROM schema_migrations "
            "WHERE migration_id = :migration_id"
        ),
        {"migration_id": MIGRATION_ID},
    ).scalar_one_or_none()
    if already_applied:
        return

    inspector = inspect(sync_connection)
    if "users" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("users")}

        if "role" not in columns:
            sync_connection.execute(
                text(
                    "ALTER TABLE users ADD COLUMN "
                    "role VARCHAR(20) NOT NULL DEFAULT 'user'"
                )
            )

        if "is_active" not in columns:
            sync_connection.execute(
                text(
                    "ALTER TABLE users ADD COLUMN "
                    f"is_active BOOLEAN NOT NULL DEFAULT {boolean_default}"
                )
            )

        sync_connection.execute(
            text("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''")
        )
        sync_connection.execute(
            text(
                "UPDATE users SET is_active = "
                f"{boolean_default} WHERE is_active IS NULL"
            )
        )

    sync_connection.execute(
        text(
            "INSERT INTO schema_migrations (migration_id) "
            "VALUES (:migration_id)"
        ),
        {"migration_id": MIGRATION_ID},
    )


async def run_migrations(connection: AsyncConnection) -> None:
    await connection.run_sync(_run_core_auth_migration)
