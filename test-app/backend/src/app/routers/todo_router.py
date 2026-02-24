"""Todo router with CRUD endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.schemas.todo import (
    ClearCompletedResponse,
    TodoCreate,
    TodoListResponse,
    TodoRead,
    TodoUpdate,
)
from app.services.todo_service import TodoService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/todos", tags=["todos"])

# Define dependency type for reuse
DbSession = Annotated["AsyncSession", Depends(get_db)]


@router.get("/", response_model=TodoListResponse)
async def list_todos(
    db: DbSession,
    filter: Literal["all", "active", "completed"] = "all",
    skip: int = 0,
    limit: int = 20,
) -> TodoListResponse:
    """List todos with optional filtering and pagination.

    Args:
        filter: Filter by completion status (all, active, completed).
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        db: Database session.

    Returns:
        Todo list with metadata.
    """
    service = TodoService(db)
    todos = await service.list(filter_by=filter, skip=skip, limit=limit)
    meta = await service.get_counts()

    return TodoListResponse(
        data=[TodoRead.model_validate(todo) for todo in todos],
        meta=meta,
    )


@router.post("/", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
async def create_todo(
    payload: TodoCreate,
    db: DbSession,
) -> TodoRead:
    """Create a new todo.

    Args:
        payload: The todo creation data.
        db: Database session.

    Returns:
        The created todo item.
    """
    service = TodoService(db)
    todo = await service.create(payload)
    return TodoRead.model_validate(todo)


@router.delete("/completed", response_model=ClearCompletedResponse)
async def clear_completed_todos(
    db: DbSession,
) -> ClearCompletedResponse:
    """Delete all completed todos.

    Args:
        db: Database session.

    Returns:
        The number of deleted todos.
    """
    service = TodoService(db)
    deleted_count = await service.clear_completed()
    return ClearCompletedResponse(deleted_count=deleted_count)


@router.get("/{todo_id}", response_model=TodoRead)
async def get_todo(
    todo_id: int,
    db: DbSession,
) -> TodoRead:
    """Get a single todo by ID.

    Args:
        todo_id: The todo ID to retrieve.
        db: Database session.

    Returns:
        The todo item.

    Raises:
        HTTPException: If todo not found.
    """
    service = TodoService(db)
    todo = await service.get_by_id(todo_id)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    return TodoRead.model_validate(todo)


@router.patch("/{todo_id}", response_model=TodoRead)
async def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    db: DbSession,
) -> TodoRead:
    """Update a todo by ID (partial update).

    Args:
        todo_id: The todo ID to update.
        payload: The update data.
        db: Database session.

    Returns:
        The updated todo item.

    Raises:
        HTTPException: If todo not found.
    """
    service = TodoService(db)
    todo = await service.update(todo_id, payload)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    return TodoRead.model_validate(todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: int,
    db: DbSession,
) -> None:
    """Delete a todo by ID.

    Args:
        todo_id: The todo ID to delete.
        db: Database session.

    Raises:
        HTTPException: If todo not found.
    """
    service = TodoService(db)
    deleted = await service.delete(todo_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
