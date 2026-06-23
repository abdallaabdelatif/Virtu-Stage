import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import select

from app.database import AsyncSessionLocal, Base, engine
from app.migrations import run_migrations
from app.models import password_reset_token as password_reset_token_model
from app.models import session as session_model
from app.models import conversation_history as conversation_history_model
from app.models import voice_analysis as voice_analysis_model
from app.models import motion_analysis as motion_analysis_model
from app.models.user import User
from app.security.passwords import hash_password, validate_password_strength


async def bootstrap_admin() -> None:
    load_dotenv()
    username = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "").strip()
    email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")

    if not username or not email or not password:
        raise RuntimeError(
            "BOOTSTRAP_ADMIN_USERNAME, BOOTSTRAP_ADMIN_EMAIL, and "
            "BOOTSTRAP_ADMIN_PASSWORD are required"
        )
    validate_password_strength(password)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await run_migrations(connection)

    async with AsyncSessionLocal() as session:
        existing_admin = await session.scalar(
            select(User).where(User.role == "admin")
        )
        if existing_admin:
            print("Admin account already exists; no changes made.")
            return

        conflicting_user = await session.scalar(
            select(User).where(
                (User.username == username) | (User.email == email)
            )
        )
        if conflicting_user:
            conflicting_user.role = "admin"
            conflicting_user.is_active = True
        else:
            session.add(
                User(
                    username=username,
                    email=email,
                    password_hash=hash_password(password),
                    first_name="System",
                    last_name="Administrator",
                    role="admin",
                    is_active=True,
                )
            )
        await session.commit()
        print("Admin account created or promoted successfully.")


if __name__ == "__main__":
    asyncio.run(bootstrap_admin())
