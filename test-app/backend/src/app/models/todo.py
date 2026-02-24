"""Todo model definition."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy needs runtime access

from sqlalchemy import Boolean, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Todo(Base):
    """SQLAlchemy model for the todos table."""

    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
