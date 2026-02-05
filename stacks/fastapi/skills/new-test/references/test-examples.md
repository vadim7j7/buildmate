# pytest Test File Examples

Patterns for generating test files for different layers of a FastAPI application.

---

## Router Test Example

```python
from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestProjectRouter:
    """Integration tests for the /projects endpoints."""

    async def test_create_project(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects/",
            json={"name": "Test Project", "description": "A description"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert "id" in data
        assert "created_at" in data

    async def test_create_project_validation_error(
        self, client: AsyncClient
    ) -> None:
        response = await client.post("/api/v1/projects/", json={})
        assert response.status_code == 422

    async def test_list_projects(self, client: AsyncClient) -> None:
        # Create two projects
        await client.post("/api/v1/projects/", json={"name": "Project 1"})
        await client.post("/api/v1/projects/", json={"name": "Project 2"})

        response = await client.get("/api/v1/projects/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    async def test_get_project(self, client: AsyncClient) -> None:
        # Create
        create_resp = await client.post(
            "/api/v1/projects/", json={"name": "Get Me"}
        )
        project_id = create_resp.json()["id"]

        # Get
        response = await client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Me"

    async def test_get_project_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/projects/99999")
        assert response.status_code == 404

    async def test_update_project(self, client: AsyncClient) -> None:
        create_resp = await client.post(
            "/api/v1/projects/", json={"name": "Before"}
        )
        project_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/v1/projects/{project_id}",
            json={"name": "After"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "After"

    async def test_delete_project(self, client: AsyncClient) -> None:
        create_resp = await client.post(
            "/api/v1/projects/", json={"name": "Delete Me"}
        )
        project_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 204
```

---

## Service Test Example

```python
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService


class TestProjectService:
    """Unit tests for ProjectService."""

    async def test_create(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        project = await service.create(ProjectCreate(name="New"))
        assert project.id is not None
        assert project.name == "New"

    async def test_list_empty(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        result = await service.list()
        assert result == []

    async def test_list_with_data(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        await service.create(ProjectCreate(name="A"))
        await service.create(ProjectCreate(name="B"))
        result = await service.list()
        assert len(result) == 2

    async def test_get_by_id(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        created = await service.create(ProjectCreate(name="Find Me"))
        found = await service.get_by_id(created.id)
        assert found is not None
        assert found.name == "Find Me"

    async def test_get_by_id_not_found(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        assert await service.get_by_id(99999) is None

    async def test_update(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        project = await service.create(ProjectCreate(name="Old"))
        updated = await service.update(project.id, ProjectUpdate(name="New"))
        assert updated is not None
        assert updated.name == "New"

    async def test_update_not_found(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        result = await service.update(99999, ProjectUpdate(name="X"))
        assert result is None

    async def test_delete(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        project = await service.create(ProjectCreate(name="Remove"))
        assert await service.delete(project.id) is True
        assert await service.get_by_id(project.id) is None

    async def test_delete_not_found(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        assert await service.delete(99999) is False
```

---

## Schema Test Example

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate


class TestProjectCreate:
    """Validation tests for ProjectCreate schema."""

    def test_valid(self) -> None:
        schema = ProjectCreate(name="Test", description="Desc")
        assert schema.name == "Test"

    def test_name_required(self) -> None:
        with pytest.raises(ValidationError):
            ProjectCreate()

    def test_description_optional(self) -> None:
        schema = ProjectCreate(name="Test")
        assert schema.description is None


class TestProjectUpdate:
    """Validation tests for ProjectUpdate schema."""

    def test_all_optional(self) -> None:
        schema = ProjectUpdate()
        assert schema.name is None

    def test_partial_update(self) -> None:
        schema = ProjectUpdate(name="Updated")
        dump = schema.model_dump(exclude_unset=True)
        assert dump == {"name": "Updated"}
```

---

## Task Test Example

```python
from __future__ import annotations

from unittest.mock import patch

from app.tasks.sync import sync_external_data


class TestSyncExternalData:
    """Tests for the sync_external_data Celery task."""

    def test_successful_sync(self) -> None:
        result = sync_external_data(resource_id=1)
        assert result["status"] == "ok"
        assert result["resource_id"] == 1

    @patch("app.tasks.sync.sync_external_data.retry")
    def test_retry_on_failure(self, mock_retry) -> None:
        mock_retry.side_effect = Exception("Retry triggered")
        # Test that the task retries on failure
        ...
```
