"""Todo service with business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from sqlalchemy import delete, func, select

from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoMeta, TodoUpdate

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class TodoService:
    """Business logic for todo operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(
        self,
        *,
        filter_by: Literal["all", "active", "completed"] = "all",
        skip: int = 0,
        limit: int = 20,
    ) -> list[Todo]:
        """List todos with optional filtering and pagination.

        Args:
            filter_by: Filter by completion status (all, active, completed).
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of todo items.
        """
        stmt = select(Todo)

        if filter_by == "active":
            stmt = stmt.where(Todo.completed.is_(False))
        elif filter_by == "completed":
            stmt = stmt.where(Todo.completed.is_(True))

        stmt = stmt.order_by(Todo.created_at.desc()).offset(skip).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, todo_id: int) -> Todo | None:
        """Get a todo by primary key.

        Args:
            todo_id: The todo ID to retrieve.

        Returns:
            The todo item or None if not found.
        """
        return await self._db.get(Todo, todo_id)

    async def create(self, payload: TodoCreate) -> Todo:
        """Create a new todo.

        Args:
            payload: The todo creation data.

        Returns:
            The created todo item.
        """
        todo = Todo(**payload.model_dump())
        self._db.add(todo)
        await self._db.commit()
        await self._db.refresh(todo)
        return todo

    async def update(self, todo_id: int, payload: TodoUpdate) -> Todo | None:
        """Update an existing todo.

        Args:
            todo_id: The todo ID to update.
            payload: The update data.

        Returns:
            The updated todo item or None if not found.
        """
        todo = await self.get_by_id(todo_id)
        if todo is None:
            return None

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(todo, field, value)

        await self._db.commit()
        await self._db.refresh(todo)
        return todo

    async def delete(self, todo_id: int) -> bool:
        """Delete a todo by ID.

        Args:
            todo_id: The todo ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        todo = await self.get_by_id(todo_id)
        if todo is None:
            return False

        await self._db.delete(todo)
        await self._db.commit()
        return True

    async def clear_completed(self) -> int:
        """Delete all completed todos.

        Returns:
            The number of deleted todos.
        """
        stmt = delete(Todo).where(Todo.completed.is_(True))
        result = await self._db.execute(stmt)
        await self._db.commit()
        return result.rowcount  # type: ignore[no-any-return,attr-defined]

    async def get_counts(self) -> TodoMeta:
        """Get todo counts by status.

        Returns:
            Meta object with total, active, and completed counts.
        """
        total_stmt = select(func.count(Todo.id))
        active_stmt = select(func.count(Todo.id)).where(Todo.completed.is_(False))
        completed_stmt = select(func.count(Todo.id)).where(Todo.completed.is_(True))

        total_result = await self._db.execute(total_stmt)
        active_result = await self._db.execute(active_stmt)
        completed_result = await self._db.execute(completed_stmt)

        return TodoMeta(
            total=total_result.scalar() or 0,
            active=active_result.scalar() or 0,
            completed=completed_result.scalar() or 0,
        )
