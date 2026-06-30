from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncConnection


MIGRATION_ID = "20260623_core_auth"
MOTION_ASSESSMENT_MIGRATION_ID = "20260625_motion_presentation_assessment"
SESSION_PROCESSING_MIGRATION_ID = "20260628_session_processing_status"
VOICE_EMOTION_REMOVAL_MIGRATION_ID = "20260628_remove_voice_emotion_fields"
REGISTRATION_IDENTITY_MIGRATION_ID = "20260628_registration_identity_uniqueness"
VOICE_SCHEMA_MIGRATION_ID = "20260628_voice_analysis_flat_schema"
VOICE_PAUSE_RATIO_NULLABLE_MIGRATION_ID = "20260628_voice_pause_ratio_nullable"
PRESENTATION_PROCESSING_MIGRATION_ID = "20260628_presentation_processing"
USER_AVATAR_MIGRATION_ID = "20260629_user_avatar"
VOICE_TRAIT_REASONS_MIGRATION_ID = "20260630_voice_trait_reasons"


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
    await connection.run_sync(_run_voice_analysis_flat_schema_migration)
    await connection.run_sync(_run_voice_pause_ratio_nullable_migration)
    await connection.run_sync(_run_registration_identity_migration)
    await connection.run_sync(_run_presentation_processing_migration)
    await connection.run_sync(_run_user_avatar_migration)
    await connection.run_sync(_run_voice_trait_reasons_migration)


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


def _run_voice_analysis_flat_schema_migration(sync_connection) -> None:
    if _migration_already_applied(sync_connection, VOICE_SCHEMA_MIGRATION_ID):
        return

    inspector = inspect(sync_connection)
    if "voice_analysis" not in inspector.get_table_names():
        _record_migration(sync_connection, VOICE_SCHEMA_MIGRATION_ID)
        return

    columns = {column["name"] for column in inspector.get_columns("voice_analysis")}
    dialect = sync_connection.dialect.name

    def add_column(name: str, definition: str) -> None:
        if name not in columns:
            sync_connection.execute(
                text(f"ALTER TABLE voice_analysis ADD COLUMN {name} {definition}")
            )
            columns.add(name)

    add_column("confidence_level", "FLOAT")
    add_column("focus_level", "FLOAT")
    add_column("voice_quality_score", "FLOAT")
    add_column("voice_quality_level", "VARCHAR(32)")
    add_column("fluency_score", "FLOAT")
    add_column("fluency_level", "VARCHAR(32)")
    add_column("energy_control_score", "FLOAT")
    add_column("energy_control_level", "VARCHAR(32)")
    add_column("articulation_score", "FLOAT")
    add_column("articulation_level", "VARCHAR(32)")
    add_column("words_per_minute", "FLOAT")
    add_column("filler_word_count", "INTEGER")
    add_column("longest_pause_sec", "FLOAT")
    add_column("confidence_feedback", "TEXT NOT NULL DEFAULT ''")
    add_column("anxiety_feedback", "TEXT NOT NULL DEFAULT ''")
    add_column("clarity_feedback", "TEXT NOT NULL DEFAULT ''")
    add_column("focus_feedback", "TEXT NOT NULL DEFAULT ''")

    if "confidence_score" in columns:
        sync_connection.execute(
            text(
                "UPDATE voice_analysis SET confidence_level = "
                "CASE WHEN confidence_score BETWEEN 0 AND 1 "
                "THEN confidence_score * 100 ELSE confidence_score END "
                "WHERE confidence_level IS NULL"
            )
        )
    if "focus_score" in columns:
        sync_connection.execute(
            text(
                "UPDATE voice_analysis SET focus_level = "
                "CASE WHEN focus_score BETWEEN 0 AND 1 "
                "THEN focus_score * 100 ELSE focus_score END "
                "WHERE focus_level IS NULL"
            )
        )
    if "speech_rate_wpm" in columns:
        sync_connection.execute(
            text(
                "UPDATE voice_analysis SET words_per_minute = speech_rate_wpm "
                "WHERE words_per_minute IS NULL"
            )
        )
    if "filler_words_count" in columns:
        sync_connection.execute(
            text(
                "UPDATE voice_analysis SET filler_word_count = filler_words_count "
                "WHERE filler_word_count IS NULL"
            )
        )
    if "longest_pause_seconds" in columns:
        sync_connection.execute(
            text(
                "UPDATE voice_analysis SET longest_pause_sec = longest_pause_seconds "
                "WHERE longest_pause_sec IS NULL"
            )
        )

    legacy_columns = [
        "confidence_score",
        "focus_score",
        "speech_rate_wpm",
        "filler_words_count",
        "longest_pause_seconds",
    ]
    for column in legacy_columns:
        if column in columns:
            if dialect == "postgresql":
                sync_connection.execute(
                    text(f"ALTER TABLE voice_analysis DROP COLUMN IF EXISTS {column}")
                )
            else:
                sync_connection.execute(
                    text(f"ALTER TABLE voice_analysis DROP COLUMN {column}")
                )

    _record_migration(sync_connection, VOICE_SCHEMA_MIGRATION_ID)


def _run_voice_pause_ratio_nullable_migration(sync_connection) -> None:
    if _migration_already_applied(
        sync_connection, VOICE_PAUSE_RATIO_NULLABLE_MIGRATION_ID
    ):
        return

    inspector = inspect(sync_connection)
    if "voice_analysis" not in inspector.get_table_names():
        _record_migration(sync_connection, VOICE_PAUSE_RATIO_NULLABLE_MIGRATION_ID)
        return

    pause_ratio_column = next(
        (
            column
            for column in inspector.get_columns("voice_analysis")
            if column["name"] == "pause_ratio"
        ),
        None,
    )
    if pause_ratio_column is None or pause_ratio_column.get("nullable", True):
        _record_migration(sync_connection, VOICE_PAUSE_RATIO_NULLABLE_MIGRATION_ID)
        return

    dialect = sync_connection.dialect.name
    if dialect == "postgresql":
        sync_connection.execute(
            text("ALTER TABLE voice_analysis ALTER COLUMN pause_ratio DROP NOT NULL")
        )
    elif dialect == "sqlite":
        _rebuild_sqlite_voice_analysis_with_nullable_pause_ratio(sync_connection)
    else:
        raise RuntimeError(
            "Unsupported database dialect for pause_ratio nullability migration: "
            f"{dialect}"
        )

    _record_migration(sync_connection, VOICE_PAUSE_RATIO_NULLABLE_MIGRATION_ID)


def _run_voice_trait_reasons_migration(sync_connection) -> None:
    if _migration_already_applied(sync_connection, VOICE_TRAIT_REASONS_MIGRATION_ID):
        return

    inspector = inspect(sync_connection)
    if "voice_analysis" not in inspector.get_table_names():
        _record_migration(sync_connection, VOICE_TRAIT_REASONS_MIGRATION_ID)
        return

    columns = {column["name"] for column in inspector.get_columns("voice_analysis")}
    json_definition = "JSON NOT NULL DEFAULT '[]'"
    for name in [
        "confidence_reasons",
        "anxiety_reasons",
        "clarity_reasons",
        "focus_reasons",
    ]:
        if name not in columns:
            sync_connection.execute(
                text(f"ALTER TABLE voice_analysis ADD COLUMN {name} {json_definition}")
            )

    _record_migration(sync_connection, VOICE_TRAIT_REASONS_MIGRATION_ID)


def _rebuild_sqlite_voice_analysis_with_nullable_pause_ratio(sync_connection) -> None:
    inspector = inspect(sync_connection)
    existing_columns = {
        column["name"] for column in inspector.get_columns("voice_analysis")
    }
    target_columns = [
        "voice_analysis_id",
        "session_id",
        "confidence_level",
        "anxiety_level",
        "clarity_level",
        "focus_level",
        "confidence_reasons",
        "anxiety_reasons",
        "clarity_reasons",
        "focus_reasons",
        "voice_quality_score",
        "voice_quality_level",
        "fluency_score",
        "fluency_level",
        "energy_control_score",
        "energy_control_level",
        "articulation_score",
        "articulation_level",
        "words_per_minute",
        "pause_ratio",
        "filler_word_count",
        "pause_count",
        "longest_pause_sec",
        "confidence_feedback",
        "anxiety_feedback",
        "clarity_feedback",
        "focus_feedback",
        "analyzed_at",
    ]
    copied_columns = [
        column for column in target_columns if column in existing_columns
    ]
    copied_column_sql = ", ".join(copied_columns)

    sync_connection.execute(text("ALTER TABLE voice_analysis RENAME TO voice_analysis_old"))
    sync_connection.execute(
        text(
            """
            CREATE TABLE voice_analysis (
                voice_analysis_id CHAR(32) NOT NULL,
                session_id CHAR(32) NOT NULL,
                confidence_level FLOAT,
                anxiety_level FLOAT,
                clarity_level FLOAT,
                focus_level FLOAT,
                confidence_reasons JSON NOT NULL DEFAULT '[]',
                anxiety_reasons JSON NOT NULL DEFAULT '[]',
                clarity_reasons JSON NOT NULL DEFAULT '[]',
                focus_reasons JSON NOT NULL DEFAULT '[]',
                voice_quality_score FLOAT,
                voice_quality_level VARCHAR(32),
                fluency_score FLOAT,
                fluency_level VARCHAR(32),
                energy_control_score FLOAT,
                energy_control_level VARCHAR(32),
                articulation_score FLOAT,
                articulation_level VARCHAR(32),
                words_per_minute FLOAT,
                pause_ratio FLOAT,
                filler_word_count INTEGER,
                pause_count INTEGER,
                longest_pause_sec FLOAT,
                confidence_feedback TEXT NOT NULL DEFAULT '',
                anxiety_feedback TEXT NOT NULL DEFAULT '',
                clarity_feedback TEXT NOT NULL DEFAULT '',
                focus_feedback TEXT NOT NULL DEFAULT '',
                analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                PRIMARY KEY (voice_analysis_id),
                FOREIGN KEY(session_id) REFERENCES training_sessions (session_id)
                    ON DELETE CASCADE,
                UNIQUE (session_id)
            )
            """
        )
    )
    sync_connection.execute(
        text(
            f"""
            INSERT INTO voice_analysis ({copied_column_sql})
            SELECT {copied_column_sql} FROM voice_analysis_old
            """
        )
    )
    sync_connection.execute(text("DROP TABLE voice_analysis_old"))
    sync_connection.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_voice_analysis_session_id "
            "ON voice_analysis (session_id)"
        )
    )


def _run_presentation_processing_migration(sync_connection) -> None:
    if _migration_already_applied(sync_connection, PRESENTATION_PROCESSING_MIGRATION_ID):
        return

    inspector = inspect(sync_connection)
    if "library_files" not in inspector.get_table_names():
        _record_migration(sync_connection, PRESENTATION_PROCESSING_MIGRATION_ID)
        return

    dialect = sync_connection.dialect.name
    timestamp_type = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"
    columns = {column["name"] for column in inspector.get_columns("library_files")}
    additions = {
        "processing_status": "VARCHAR(20) NOT NULL DEFAULT 'queued'",
        "slide_count": "INTEGER",
        "processing_error": "TEXT",
        "processed_at": timestamp_type,
    }
    for name, definition in additions.items():
        if name not in columns:
            sync_connection.execute(
                text(f"ALTER TABLE library_files ADD COLUMN {name} {definition}")
            )

    _record_migration(sync_connection, PRESENTATION_PROCESSING_MIGRATION_ID)


def _run_user_avatar_migration(sync_connection) -> None:
    if _migration_already_applied(sync_connection, USER_AVATAR_MIGRATION_ID):
        return

    inspector = inspect(sync_connection)
    if "users" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("users")}
        if "avatar_key" not in columns:
            sync_connection.execute(
                text("ALTER TABLE users ADD COLUMN avatar_key VARCHAR(500)")
            )

    _record_migration(sync_connection, USER_AVATAR_MIGRATION_ID)
