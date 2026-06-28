import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["INTERNAL_API_KEY"] = "test-internal-key"

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, get_session  # noqa: E402
from app.main import app  # noqa: E402

INTERNAL_HEADERS = {"X-Internal-API-Key": "test-internal-key"}


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        from app.migrations import run_migrations

        await run_migrations(conn)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_engine):
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user_id(client: AsyncClient):
    response = await client.post(
        "/users",
        json={
            "username": "session_tester",
            "email": "session@test.com",
            "password": "Test@1234",
            "first_name": "Session",
            "last_name": "Tester",
            "gender": "male",
        },
    )
    assert response.status_code == 201
    return response.json()["user_id"]
