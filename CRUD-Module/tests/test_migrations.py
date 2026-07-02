import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.migrations import (
    _run_user_avatar_migration,
    _run_voice_pause_fields_migration,
    run_migrations,
)


@pytest.mark.asyncio
async def test_voice_pause_fields_migration_adds_missing_legacy_columns():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "CREATE TABLE voice_analysis ("
                    "voice_analysis_id CHAR(32) PRIMARY KEY"
                    ")"
                )
            )

            await connection.run_sync(_run_voice_pause_fields_migration)
            await connection.run_sync(_run_voice_pause_fields_migration)

            columns = await connection.run_sync(
                lambda sync_connection: {
                    column["name"]
                    for column in inspect(sync_connection).get_columns(
                        "voice_analysis"
                    )
                }
            )
            assert {"pause_ratio", "pause_count"}.issubset(columns)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_voice_pause_ratio_migration_relaxes_sqlite_not_null():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.execute(text("PRAGMA foreign_keys=ON"))
            await connection.execute(
                text(
                    """
                    CREATE TABLE training_sessions (
                        session_id CHAR(32) NOT NULL,
                        PRIMARY KEY (session_id)
                    )
                    """
                )
            )
            await connection.execute(
                text(
                    """
                    CREATE TABLE voice_analysis (
                        voice_analysis_id CHAR(32) NOT NULL,
                        session_id CHAR(32) NOT NULL,
                        pause_ratio FLOAT NOT NULL,
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

            await run_migrations(connection)

            pause_ratio_column = await connection.run_sync(
                lambda sync_connection: next(
                    column
                    for column in inspect(sync_connection).get_columns(
                        "voice_analysis"
                    )
                    if column["name"] == "pause_ratio"
                )
            )
            assert pause_ratio_column["nullable"] is True

            await connection.execute(
                text(
                    """
                    INSERT INTO training_sessions (session_id)
                    VALUES ('session0000000000000000000000000')
                    """
                )
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO voice_analysis (
                        voice_analysis_id,
                        session_id,
                        pause_ratio
                    )
                    VALUES (
                        'voice000000000000000000000000000',
                        'session0000000000000000000000000',
                        NULL
                    )
                    """
                )
            )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_user_avatar_migration_adds_column_to_existing_users_table():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "CREATE TABLE users ("
                    "user_id CHAR(32) PRIMARY KEY, username VARCHAR(100) NOT NULL"
                    ")"
                )
            )
            await connection.run_sync(_run_user_avatar_migration)
            columns = await connection.run_sync(
                lambda sync_connection: {
                    column["name"]
                    for column in inspect(sync_connection).get_columns("users")
                }
            )
            assert "avatar_key" in columns
    finally:
        await engine.dispose()
