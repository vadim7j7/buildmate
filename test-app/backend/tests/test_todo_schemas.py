"""Tests for todo Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.todo import (
    ClearCompletedResponse,
    TodoCreate,
    TodoListResponse,
    TodoMeta,
    TodoRead,
    TodoUpdate,
)


class TestTodoCreate:
    """Tests for TodoCreate schema validation."""

    def test_valid_with_title(self) -> None:
        """Test creating schema with valid title."""
        schema = TodoCreate(title="Test todo")
        assert schema.title == "Test todo"

    def test_missing_title(self) -> None:
        """Test that title is required."""
        with pytest.raises(ValidationError) as exc_info:
            TodoCreate()  # type: ignore
        assert "title" in str(exc_info.value)

    def test_empty_title(self) -> None:
        """Test that empty title is valid (business logic may reject)."""
        schema = TodoCreate(title="")
        assert schema.title == ""

    def test_extra_fields_ignored(self) -> None:
        """Test that extra fields are ignored."""
        schema = TodoCreate(title="Test", extra="ignored")  # type: ignore
        assert schema.title == "Test"
        assert not hasattr(schema, "extra")


class TestTodoUpdate:
    """Tests for TodoUpdate schema validation."""

    def test_empty_update(self) -> None:
        """Test that all fields are optional."""
        schema = TodoUpdate()
        assert schema.title is None
        assert schema.completed is None

    def test_update_title_only(self) -> None:
        """Test updating only title."""
        schema = TodoUpdate(title="Updated title")
        assert schema.title == "Updated title"
        assert schema.completed is None

    def test_update_completed_only(self) -> None:
        """Test updating only completed status."""
        schema = TodoUpdate(completed=True)
        assert schema.title is None
        assert schema.completed is True

    def test_update_both_fields(self) -> None:
        """Test updating both fields."""
        schema = TodoUpdate(title="Updated", completed=True)
        assert schema.title == "Updated"
        assert schema.completed is True

    def test_completed_coercion(self) -> None:
        """Test that completed coerces string to boolean."""
        # Pydantic coerces "true" to True
        schema = TodoUpdate(completed="true")  # type: ignore
        assert schema.completed is True


class TestTodoRead:
    """Tests for TodoRead schema validation."""

    def test_valid_todo_read(self) -> None:
        """Test creating a valid TodoRead schema."""
        schema = TodoRead(
            id=1,
            title="Test todo",
            completed=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert schema.id == 1
        assert schema.title == "Test todo"
        assert schema.completed is False
        assert isinstance(schema.created_at, datetime)
        assert isinstance(schema.updated_at, datetime)

    def test_missing_required_fields(self) -> None:
        """Test that all fields are required."""
        with pytest.raises(ValidationError) as exc_info:
            TodoRead(title="Test")  # type: ignore
        errors = str(exc_info.value)
        assert "id" in errors
        assert "completed" in errors
        assert "created_at" in errors
        assert "updated_at" in errors

    def test_invalid_types(self) -> None:
        """Test that field types are validated."""
        with pytest.raises(ValidationError):
            TodoRead(
                id="not_an_int",  # type: ignore
                title="Test",
                completed=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )


class TestTodoMeta:
    """Tests for TodoMeta schema validation."""

    def test_valid_meta(self) -> None:
        """Test creating valid meta schema."""
        schema = TodoMeta(total=10, active=7, completed=3)
        assert schema.total == 10
        assert schema.active == 7
        assert schema.completed == 3

    def test_zero_counts(self) -> None:
        """Test meta with zero counts."""
        schema = TodoMeta(total=0, active=0, completed=0)
        assert schema.total == 0
        assert schema.active == 0
        assert schema.completed == 0

    def test_missing_fields(self) -> None:
        """Test that all fields are required."""
        with pytest.raises(ValidationError) as exc_info:
            TodoMeta(total=10)  # type: ignore
        errors = str(exc_info.value)
        assert "active" in errors
        assert "completed" in errors

    def test_count_coercion(self) -> None:
        """Test that counts coerce strings to integers."""
        # Pydantic coerces numeric strings to integers
        schema = TodoMeta(total="10", active=5, completed=5)  # type: ignore
        assert schema.total == 10


class TestTodoListResponse:
    """Tests for TodoListResponse schema validation."""

    def test_valid_list_response(self) -> None:
        """Test creating valid list response."""
        schema = TodoListResponse(
            data=[
                TodoRead(
                    id=1,
                    title="Test",
                    completed=False,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            ],
            meta=TodoMeta(total=1, active=1, completed=0),
        )
        assert len(schema.data) == 1
        assert schema.meta.total == 1

    def test_empty_list(self) -> None:
        """Test list response with empty data."""
        schema = TodoListResponse(
            data=[],
            meta=TodoMeta(total=0, active=0, completed=0),
        )
        assert schema.data == []
        assert schema.meta.total == 0

    def test_multiple_todos(self) -> None:
        """Test list response with multiple todos."""
        now = datetime.now()
        schema = TodoListResponse(
            data=[
                TodoRead(
                    id=1,
                    title="Todo 1",
                    completed=False,
                    created_at=now,
                    updated_at=now,
                ),
                TodoRead(
                    id=2,
                    title="Todo 2",
                    completed=True,
                    created_at=now,
                    updated_at=now,
                ),
            ],
            meta=TodoMeta(total=2, active=1, completed=1),
        )
        assert len(schema.data) == 2
        assert schema.meta.total == 2

    def test_missing_meta(self) -> None:
        """Test that meta is required."""
        with pytest.raises(ValidationError) as exc_info:
            TodoListResponse(data=[])  # type: ignore
        assert "meta" in str(exc_info.value)


class TestClearCompletedResponse:
    """Tests for ClearCompletedResponse schema validation."""

    def test_valid_response(self) -> None:
        """Test creating valid clear completed response."""
        schema = ClearCompletedResponse(deleted_count=5)
        assert schema.deleted_count == 5

    def test_zero_deleted(self) -> None:
        """Test response with zero deleted."""
        schema = ClearCompletedResponse(deleted_count=0)
        assert schema.deleted_count == 0

    def test_missing_count(self) -> None:
        """Test that deleted_count is required."""
        with pytest.raises(ValidationError) as exc_info:
            ClearCompletedResponse()  # type: ignore
        assert "deleted_count" in str(exc_info.value)

    def test_count_coercion(self) -> None:
        """Test that deleted_count coerces strings to integers."""
        # Pydantic coerces numeric strings to integers
        schema = ClearCompletedResponse(deleted_count="5")  # type: ignore
        assert schema.deleted_count == 5


class TestTodoSchemasParametrized:
    """Parametrized validation tests for todo schemas."""

    @pytest.mark.parametrize(
        ("payload", "is_valid"),
        [
            ({"title": "Valid todo"}, True),
            ({"title": "Valid with spaces"}, True),
            ({"title": ""}, True),  # Empty allowed by schema
            ({}, False),  # Missing title
        ],
        ids=["valid", "with-spaces", "empty-title", "missing-title"],
    )
    def test_todo_create_validation(self, payload: dict, is_valid: bool) -> None:
        """Test TodoCreate validation with various inputs."""
        if is_valid:
            schema = TodoCreate(**payload)
            assert schema.title == payload["title"]
        else:
            with pytest.raises(ValidationError):
                TodoCreate(**payload)

    @pytest.mark.parametrize(
        ("payload", "is_valid"),
        [
            ({}, True),  # All optional
            ({"title": "Updated"}, True),
            ({"completed": True}, True),
            ({"title": "Updated", "completed": True}, True),
            ({"completed": "not_bool"}, False),
        ],
        ids=[
            "empty",
            "title-only",
            "completed-only",
            "both",
            "invalid-completed",
        ],
    )
    def test_todo_update_validation(self, payload: dict, is_valid: bool) -> None:
        """Test TodoUpdate validation with various inputs."""
        if is_valid:
            TodoUpdate(**payload)
            assert True  # Just validate it doesn't raise
        else:
            with pytest.raises(ValidationError):
                TodoUpdate(**payload)
