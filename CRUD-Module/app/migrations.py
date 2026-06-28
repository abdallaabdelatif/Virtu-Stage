from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncConnection


MIGRATION_ID = "20260623_core_auth"
MOTION_ASSESSMENT_MIGRATION_ID = "20260625_motion_presentation_assessment"
SESSION_PROCESSING_MIGRATION_ID = "20260628_session_processing_status"
VOICE_EMOTION_REMOVAL_MIGRATION_ID = "20260628_remove_voice_emotion_fields"
REGISTRATION_IDENTITY_MIGRATION_ID = "20260628_registration_identity_uniqueness"


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
    await connection.run_sync(_run_motion_assessment_migration)
    await connection.run_sync(_run_session_processing_migration)
    await connection.run_sync(_run_voice_emotion_removal_migration)
    await connection.run_sync(_run_registration_identity_migration)


def _run_motion_assessment_migration(sync_connection) -> None:
    dialect = sync_connection.dialect.name
    timestamp_type = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"

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
        {"migration_id": MOTION_ASSESSMENT_MIGRATION_ID},
    ).scalar_one_or_none()
    if already_applied:
        return

    inspector = inspect(sync_connection)
    if "motion_analysis" not in inspector.get_table_names():
        sync_connection.execute(
            text(
                "INSERT INTO schema_migrations (migration_id) VALUES (:migration_id)"
            ),
            {"migration_id": MOTION_ASSESSMENT_MIGRATION_ID},
        )
        return

    columns = {column["name"] for column in inspector.get_columns("motion_analysis")}
    json_type = "JSON" if dialect == "postgresql" else "TEXT"

    if "presentation_assessment" not in columns:
        sync_connection.execute(
            text(
                f"ALTER TABLE motion_analysis ADD COLUMN presentation_assessment {json_type}"
            )
        )
    if "recommendations" not in columns:
        sync_connection.execute(
            text(f"ALTER TABLE motion_analysis ADD COLUMN recommendations {json_type}")
        )
    if "dominant_posture_type" not in columns:
        sync_connection.execute(
            text("ALTER TABLE motion_analysis ADD COLUMN dominant_posture_type VARCHAR(64)")
        )
    if "session_metrics" not in columns:
        sync_connection.execute(
            text(f"ALTER TABLE motion_analysis ADD COLUMN session_metrics {json_type}")
        )

    sync_connection.execute(
        text("INSERT INTO schema_migrations (migration_id) VALUES (:migration_id)"),
        {"migration_id": MOTION_ASSESSMENT_MIGRATION_ID},
    )


def _ensure_schema_migrations_table(sync_connection) -> None:
    dialect = sync_connection.dialect.name
    timestamp_type = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"
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


def _migration_already_applied(sync_connection, migration_id: str) -> bool:
    _ensure_schema_migrations_table(sync_connection)
    return (
        sync_connection.execute(
            text(
                "SELECT migration_id FROM schema_migrations "
                "WHERE migration_id = :migration_id"
            ),
            {"migration_id": migration_id},
        ).scalar_one_or_none()
        is not None
    )


def _record_migration(sync_connection, migration_id: str) -> None:
    sync_connection.execute(
        text("INSERT INTO schema_migrations (migration_id) VALUES (:migration_id)"),
        {"migration_id": migration_id},
    )


def _run_session_processing_migration(sync_connection) -> None:
    if _migration_already_applied(sync_connection, SESSION_PROCESSING_MIGRATION_ID):
        return

    dialect = sync_connection.dialect.name
    if dialect == "postgresql":
        sync_connection.execute(
            text(
                "ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'processing'"
            )
        )
    # SQLite stores enum values as plain strings; no enum alteration needed.

    _record_migration(sync_connection, SESSION_PROCESSING_MIGRATION_ID)


def _run_voice_emotion_removal_migration(sync_connection) -> None:
    if _migration_already_applied(sync_connection, VOICE_EMOTION_REMOVAL_MIGRATION_ID):
        return

    inspector = inspect(sync_connection)
    if "voice_analysis" not in inspector.get_table_names():
        _record_migration(sync_connection, VOICE_EMOTION_REMOVAL_MIGRATION_ID)
        return

    columns = {column["name"] for column in inspector.get_columns("voice_analysis")}
    emotion_columns = [
        "emotion_neutral",
        "emotion_happy",
        "emotion_sad",
        "emotion_angry",
        "dominant_emotion",
    ]
    dialect = sync_connection.dialect.name
    for column in emotion_columns:
        if column in columns:
            if dialect == "postgresql":
                sync_connection.execute(
                    text(f"ALTER TABLE voice_analysis DROP COLUMN IF EXISTS {column}")
                )
            else:
                sync_connection.execute(
                    text(f"ALTER TABLE voice_analysis DROP COLUMN {column}")
                )

    _record_migration(sync_connection, VOICE_EMOTION_REMOVAL_MIGRATION_ID)


def _run_registration_identity_migration(sync_connection) -> None:
    if _migration_already_applied(
        sync_connection, REGISTRATION_IDENTITY_MIGRATION_ID
    ):
        return

    inspector = inspect(sync_connection)
    if "users" not in inspector.get_table_names():
        _record_migration(sync_connection, REGISTRATION_IDENTITY_MIGRATION_ID)
        return

    duplicate_username = sync_connection.execute(
        text(
            "SELECT lower(username) FROM users GROUP BY lower(username) "
            "HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).scalar_one_or_none()
    duplicate_email = sync_connection.execute(
        text(
            "SELECT lower(email) FROM users GROUP BY lower(email) "
            "HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).scalar_one_or_none()
    if duplicate_username or duplicate_email:
        raise RuntimeError(
            "Cannot enforce case-insensitive registration uniqueness while "
            "case-variant duplicate users exist"
        )

    sync_connection.execute(text("UPDATE users SET email = lower(trim(email))"))
    sync_connection.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username_ci "
            "ON users (lower(username))"
        )
    )
    sync_connection.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email_ci "
            "ON users (lower(email))"
        )
    )
    _record_migration(sync_connection, REGISTRATION_IDENTITY_MIGRATION_ID)
