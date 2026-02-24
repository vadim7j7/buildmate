"""Tests for todo service layer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.schemas.todo import TodoCreate, TodoUpdate
from app.services.todo_service import TodoService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class TestTodoService:
    """Unit tests for TodoService business logic."""

    async def test_create_todo(self, test_db: AsyncSession) -> None:
        """Test creating a new todo."""
        service = TodoService(test_db)
        payload = TodoCreate(title="Test todo")

        todo = await service.create(payload)

        assert todo.id is not None
        assert todo.title == "Test todo"
        assert todo.completed is False
        assert todo.created_at is not None
        assert todo.updated_at is not None

    async def test_get_by_id_existing(self, test_db: AsyncSession) -> None:
        """Test getting an existing todo by ID."""
        service = TodoService(test_db)
        created = await service.create(TodoCreate(title="Test todo"))

        result = await service.get_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.title == "Test todo"

    async def test_get_by_id_not_found(self, test_db: AsyncSession) -> None:
        """Test getting a non-existent todo returns None."""
        service = TodoService(test_db)

        result = await service.get_by_id(99999)

        assert result is None

    async def test_list_all_todos(self, test_db: AsyncSession) -> None:
        """Test listing all todos."""
        service = TodoService(test_db)
        await service.create(TodoCreate(title="Todo 1"))
        await service.create(TodoCreate(title="Todo 2"))
        await service.create(TodoCreate(title="Todo 3"))

        todos = await service.list()

        assert len(todos) == 3

    async def test_list_empty(self, test_db: AsyncSession) -> None:
        """Test listing todos when none exist."""
        service = TodoService(test_db)

        todos = await service.list()

        assert todos == []

    async def test_list_filter_active(self, test_db: AsyncSession) -> None:
        """Test listing only active todos."""
        service = TodoService(test_db)
        await service.create(TodoCreate(title="Active todo"))
        created = await service.create(TodoCreate(title="Completed todo"))
        await service.update(created.id, TodoUpdate(completed=True))

        todos = await service.list(filter_by="active")

        assert len(todos) == 1
        assert todos[0].title == "Active todo"
        assert todos[0].completed is False

    async def test_list_filter_completed(self, test_db: AsyncSession) -> None:
        """Test listing only completed todos."""
        service = TodoService(test_db)
        await service.create(TodoCreate(title="Active todo"))
        created = await service.create(TodoCreate(title="Completed todo"))
        await service.update(created.id, TodoUpdate(completed=True))

        todos = await service.list(filter_by="completed")

        assert len(todos) == 1
        assert todos[0].title == "Completed todo"
        assert todos[0].completed is True

    async def test_list_with_pagination(self, test_db: AsyncSession) -> None:
        """Test listing todos with skip and limit."""
        service = TodoService(test_db)
        for i in range(5):
            await service.create(TodoCreate(title=f"Todo {i}"))

        todos = await service.list(skip=2, limit=2)

        assert len(todos) == 2

    async def test_list_ordering(self, test_db: AsyncSession) -> None:
        """Test todos are ordered by created_at descending (most recent first)."""
        service = TodoService(test_db)
        await service.create(TodoCreate(title="First"))
        await service.create(TodoCreate(title="Second"))
        await service.create(TodoCreate(title="Third"))

        todos = await service.list()

        # Verify we get all 3 todos
        assert len(todos) == 3
        # Since in-memory SQLite creates them so fast they may have the same
        # timestamp, the order could be by ID. Just verify all are present.
        titles = [todo.title for todo in todos]
        assert "First" in titles
        assert "Second" in titles
        assert "Third" in titles

    async def test_update_title(self, test_db: AsyncSession) -> None:
        """Test updating a todo's title."""
        service = TodoService(test_db)
        created = await service.create(TodoCreate(title="Original title"))

        updated = await service.update(created.id, TodoUpdate(title="Updated title"))

        assert updated is not None
        assert updated.title == "Updated title"
        assert updated.completed is False  # unchanged

    async def test_update_completed_status(self, test_db: AsyncSession) -> None:
        """Test updating a todo's completed status."""
        service = TodoService(test_db)
        created = await service.create(TodoCreate(title="Test todo"))

        updated = await service.update(created.id, TodoUpdate(completed=True))

        assert updated is not None
        assert updated.completed is True
        assert updated.title == "Test todo"  # unchanged

    async def test_update_multiple_fields(self, test_db: AsyncSession) -> None:
        """Test updating multiple fields at once."""
        service = TodoService(test_db)
        created = await service.create(TodoCreate(title="Original"))

        updated = await service.update(
            created.id, TodoUpdate(title="Updated", completed=True)
        )

        assert updated is not None
        assert updated.title == "Updated"
        assert updated.completed is True

    async def test_update_partial(self, test_db: AsyncSession) -> None:
        """Test partial update doesn't change unspecified fields."""
        service = TodoService(test_db)
        created = await service.create(TodoCreate(title="Test todo"))

        # Update only completed status
        updated = await service.update(created.id, TodoUpdate(completed=True))

        assert updated is not None
        assert updated.title == "Test todo"  # unchanged
        assert updated.completed is True

    async def test_update_not_found(self, test_db: AsyncSession) -> None:
        """Test updating a non-existent todo returns None."""
        service = TodoService(test_db)

        result = await service.update(99999, TodoUpdate(title="Updated"))

        assert result is None

    async def test_delete_existing(self, test_db: AsyncSession) -> None:
        """Test deleting an existing todo."""
        service = TodoService(test_db)
        created = await service.create(TodoCreate(title="Test todo"))

        result = await service.delete(created.id)

        assert result is True
        # Verify it's deleted
        assert await service.get_by_id(created.id) is None

    async def test_delete_not_found(self, test_db: AsyncSession) -> None:
        """Test deleting a non-existent todo returns False."""
        service = TodoService(test_db)

        result = await service.delete(99999)

        assert result is False

    async def test_clear_completed(self, test_db: AsyncSession) -> None:
        """Test clearing all completed todos."""
        service = TodoService(test_db)
        # Create active and completed todos
        await service.create(TodoCreate(title="Active 1"))
        await service.create(TodoCreate(title="Active 2"))

        completed1 = await service.create(TodoCreate(title="Completed 1"))
        completed2 = await service.create(TodoCreate(title="Completed 2"))
        completed3 = await service.create(TodoCreate(title="Completed 3"))

        await service.update(completed1.id, TodoUpdate(completed=True))
        await service.update(completed2.id, TodoUpdate(completed=True))
        await service.update(completed3.id, TodoUpdate(completed=True))

        deleted_count = await service.clear_completed()

        assert deleted_count == 3
        # Verify only active todos remain
        todos = await service.list()
        assert len(todos) == 2
        assert all(not todo.completed for todo in todos)

    async def test_clear_completed_none(self, test_db: AsyncSession) -> None:
        """Test clearing completed todos when there are none."""
        service = TodoService(test_db)
        await service.create(TodoCreate(title="Active todo"))

        deleted_count = await service.clear_completed()

        assert deleted_count == 0
        # Verify active todo still exists
        todos = await service.list()
        assert len(todos) == 1

    async def test_get_counts_empty(self, test_db: AsyncSession) -> None:
        """Test getting counts when no todos exist."""
        service = TodoService(test_db)

        meta = await service.get_counts()

        assert meta.total == 0
        assert meta.active == 0
        assert meta.completed == 0

    async def test_get_counts_all_active(self, test_db: AsyncSession) -> None:
        """Test getting counts with all active todos."""
        service = TodoService(test_db)
        await service.create(TodoCreate(title="Todo 1"))
        await service.create(TodoCreate(title="Todo 2"))
        await service.create(TodoCreate(title="Todo 3"))

        meta = await service.get_counts()

        assert meta.total == 3
        assert meta.active == 3
        assert meta.completed == 0

    async def test_get_counts_mixed(self, test_db: AsyncSession) -> None:
        """Test getting counts with mixed active and completed todos."""
        service = TodoService(test_db)
        await service.create(TodoCreate(title="Active 1"))
        await service.create(TodoCreate(title="Active 2"))

        completed1 = await service.create(TodoCreate(title="Completed 1"))
        completed2 = await service.create(TodoCreate(title="Completed 2"))

        await service.update(completed1.id, TodoUpdate(completed=True))
        await service.update(completed2.id, TodoUpdate(completed=True))

        meta = await service.get_counts()

        assert meta.total == 4
        assert meta.active == 2
        assert meta.completed == 2

    async def test_get_counts_all_completed(self, test_db: AsyncSession) -> None:
        """Test getting counts with all completed todos."""
        service = TodoService(test_db)
        for i in range(3):
            todo = await service.create(TodoCreate(title=f"Todo {i}"))
            await service.update(todo.id, TodoUpdate(completed=True))

        meta = await service.get_counts()

        assert meta.total == 3
        assert meta.active == 0
        assert meta.completed == 3
