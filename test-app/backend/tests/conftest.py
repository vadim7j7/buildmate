"""Pytest configuration and fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import create_app

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database override."""
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
