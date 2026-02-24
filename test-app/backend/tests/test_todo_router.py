"""Tests for todo router endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import AsyncClient


class TestTodoRouter:
    """Test cases for todo router endpoints."""

    async def test_create_todo(self, client: AsyncClient) -> None:
        """Test creating a new todo."""
        response = await client.post(
            "/api/v1/todos/",
            json={"title": "Test todo"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test todo"
        assert data["completed"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_list_todos_empty(self, client: AsyncClient) -> None:
        """Test listing todos when empty."""
        response = await client.get("/api/v1/todos/")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["meta"]["total"] == 0
        assert data["meta"]["active"] == 0
        assert data["meta"]["completed"] == 0

    async def test_list_todos_with_items(self, client: AsyncClient) -> None:
        """Test listing todos with items."""
        # Create some todos
        await client.post("/api/v1/todos/", json={"title": "Todo 1"})
        await client.post("/api/v1/todos/", json={"title": "Todo 2"})

        response = await client.get("/api/v1/todos/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["meta"]["total"] == 2
        assert data["meta"]["active"] == 2
        assert data["meta"]["completed"] == 0

    async def test_list_todos_filter_active(self, client: AsyncClient) -> None:
        """Test filtering todos by active status."""
        # Create active and completed todos
        await client.post("/api/v1/todos/", json={"title": "Active todo"})
        create_response = await client.post(
            "/api/v1/todos/", json={"title": "Completed todo"}
        )
        todo_id = create_response.json()["id"]
        await client.patch(f"/api/v1/todos/{todo_id}", json={"completed": True})

        response = await client.get("/api/v1/todos/?filter=active")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "Active todo"

    async def test_list_todos_filter_completed(self, client: AsyncClient) -> None:
        """Test filtering todos by completed status."""
        # Create active and completed todos
        await client.post("/api/v1/todos/", json={"title": "Active todo"})
        create_response = await client.post(
            "/api/v1/todos/", json={"title": "Completed todo"}
        )
        todo_id = create_response.json()["id"]
        await client.patch(f"/api/v1/todos/{todo_id}", json={"completed": True})

        response = await client.get("/api/v1/todos/?filter=completed")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "Completed todo"

    async def test_get_todo(self, client: AsyncClient) -> None:
        """Test getting a single todo by ID."""
        create_response = await client.post(
            "/api/v1/todos/", json={"title": "Test todo"}
        )
        todo_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Test todo"

    async def test_get_todo_not_found(self, client: AsyncClient) -> None:
        """Test getting a non-existent todo."""
        response = await client.get("/api/v1/todos/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Todo not found"

    async def test_update_todo_title(self, client: AsyncClient) -> None:
        """Test updating a todo's title."""
        create_response = await client.post(
            "/api/v1/todos/", json={"title": "Original title"}
        )
        todo_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/todos/{todo_id}", json={"title": "Updated title"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated title"

    async def test_update_todo_completed(self, client: AsyncClient) -> None:
        """Test marking a todo as completed."""
        create_response = await client.post(
            "/api/v1/todos/", json={"title": "Test todo"}
        )
        todo_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/todos/{todo_id}", json={"completed": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True

    async def test_update_todo_not_found(self, client: AsyncClient) -> None:
        """Test updating a non-existent todo."""
        response = await client.patch(
            "/api/v1/todos/999", json={"title": "Updated title"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Todo not found"

    async def test_delete_todo(self, client: AsyncClient) -> None:
        """Test deleting a todo."""
        create_response = await client.post(
            "/api/v1/todos/", json={"title": "Test todo"}
        )
        todo_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/todos/{todo_id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(f"/api/v1/todos/{todo_id}")
        assert get_response.status_code == 404

    async def test_delete_todo_not_found(self, client: AsyncClient) -> None:
        """Test deleting a non-existent todo."""
        response = await client.delete("/api/v1/todos/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Todo not found"

    async def test_clear_completed_todos(self, client: AsyncClient) -> None:
        """Test clearing all completed todos."""
        # Create active and completed todos
        await client.post("/api/v1/todos/", json={"title": "Active todo"})
        for i in range(3):
            create_response = await client.post(
                "/api/v1/todos/", json={"title": f"Completed todo {i}"}
            )
            todo_id = create_response.json()["id"]
            await client.patch(f"/api/v1/todos/{todo_id}", json={"completed": True})

        response = await client.delete("/api/v1/todos/completed")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 3

        # Verify only active todo remains
        list_response = await client.get("/api/v1/todos/")
        list_data = list_response.json()
        assert len(list_data["data"]) == 1
        assert list_data["data"][0]["title"] == "Active todo"

    async def test_clear_completed_todos_none(self, client: AsyncClient) -> None:
        """Test clearing completed todos when there are none."""
        await client.post("/api/v1/todos/", json={"title": "Active todo"})

        response = await client.delete("/api/v1/todos/completed")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 0
