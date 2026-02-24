"""Todo Pydantic schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Pydantic needs runtime access

from pydantic import BaseModel, ConfigDict


class TodoBase(BaseModel):
    """Shared fields for todo schemas."""

    title: str


class TodoCreate(TodoBase):
    """Schema for creating a todo."""


class TodoUpdate(BaseModel):
    """Schema for updating a todo (all fields optional)."""

    title: str | None = None
    completed: bool | None = None


class TodoRead(TodoBase):
    """Schema for reading a todo (includes DB fields)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    completed: bool
    created_at: datetime
    updated_at: datetime


class TodoMeta(BaseModel):
    """Meta information for todo list response."""

    total: int
    active: int
    completed: int


class TodoListResponse(BaseModel):
    """Response schema for listing todos with metadata."""

    data: list[TodoRead]
    meta: TodoMeta


class ClearCompletedResponse(BaseModel):
    """Response schema for clearing completed todos."""

    deleted_count: int
