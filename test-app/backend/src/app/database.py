"""Database setup with async SQLAlchemy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session with automatic cleanup."""
    async with async_session() as session:
        yield session


async def create_tables() -> None:
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
