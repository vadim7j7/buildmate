# pytest + httpx Async Test Patterns

Patterns for testing FastAPI applications with pytest, pytest-asyncio, and httpx.

---

## conftest.py Setup

```python
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import create_app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_db(engine):
    """Provide a transactional test database session."""
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            yield session
        await session.rollback()


@pytest.fixture
async def client(test_db: AsyncSession):
    """Async HTTP client with test database override."""
    app = create_app()

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

---

## pyproject.toml Configuration

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --tb=short"
```

---

## Router Test Pattern (Integration)

```python
from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestProjectRouter:
    """Integration tests for the /projects endpoints."""

    async def test_create_project(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects/",
            json={"name": "New Project", "description": "A test project"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Project"
        assert data["description"] == "A test project"
        assert "id" in data
        assert "created_at" in data

    async def test_create_project_missing_required_field(
        self, client: AsyncClient
    ) -> None:
        response = await client.post("/api/v1/projects/", json={})
        assert response.status_code == 422

    async def test_list_projects_empty(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/projects/")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_projects_with_pagination(
        self, client: AsyncClient
    ) -> None:
        # Create 3 projects
        for i in range(3):
            await client.post(
                "/api/v1/projects/", json={"name": f"Project {i}"}
            )

        response = await client.get("/api/v1/projects/?skip=0&limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_get_project(self, client: AsyncClient) -> None:
        # Create
        create_resp = await client.post(
            "/api/v1/projects/", json={"name": "Test"}
        )
        project_id = create_resp.json()["id"]

        # Get
        response = await client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()["id"] == project_id

    async def test_get_project_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/projects/99999")
        assert response.status_code == 404

    async def test_update_project(self, client: AsyncClient) -> None:
        create_resp = await client.post(
            "/api/v1/projects/", json={"name": "Original"}
        )
        project_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/v1/projects/{project_id}", json={"name": "Updated"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    async def test_delete_project(self, client: AsyncClient) -> None:
        create_resp = await client.post(
            "/api/v1/projects/", json={"name": "To Delete"}
        )
        project_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 204

        # Verify deleted
        get_resp = await client.get(f"/api/v1/projects/{project_id}")
        assert get_resp.status_code == 404
```

---

## Service Test Pattern (Unit)

```python
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService


class TestProjectService:
    """Unit tests for ProjectService."""

    async def test_create_and_retrieve(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        project = await service.create(ProjectCreate(name="Test"))

        retrieved = await service.get_by_id(project.id)
        assert retrieved is not None
        assert retrieved.name == "Test"

    async def test_list_with_pagination(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        for i in range(5):
            await service.create(ProjectCreate(name=f"Project {i}"))

        page = await service.list(skip=2, limit=2)
        assert len(page) == 2

    async def test_update_partial(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        project = await service.create(
            ProjectCreate(name="Original", description="Desc")
        )

        updated = await service.update(
            project.id, ProjectUpdate(name="New Name")
        )
        assert updated is not None
        assert updated.name == "New Name"
        assert updated.description == "Desc"  # unchanged

    async def test_delete_existing(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        project = await service.create(ProjectCreate(name="To Delete"))

        assert await service.delete(project.id) is True
        assert await service.get_by_id(project.id) is None

    async def test_delete_nonexistent(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        assert await service.delete(99999) is False
```

---

## Parametrized Test Pattern

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.project import ProjectCreate


class TestProjectCreateValidation:
    """Parametrized validation tests for ProjectCreate schema."""

    @pytest.mark.parametrize(
        ("payload", "is_valid"),
        [
            ({"name": "Valid"}, True),
            ({"name": "Valid", "description": "Desc"}, True),
            ({"name": ""}, False),
            ({}, False),
        ],
        ids=["name-only", "name-and-desc", "empty-name", "missing-name"],
    )
    def test_validation(self, payload: dict, is_valid: bool) -> None:
        if is_valid:
            schema = ProjectCreate(**payload)
            assert schema.name == payload["name"]
        else:
            with pytest.raises(ValidationError):
                ProjectCreate(**payload)
```

---

## Async Fixture Patterns

```python
from __future__ import annotations

import pytest


@pytest.fixture
async def sample_project(test_db):
    """Create a sample project for testing."""
    from app.models.project import Project

    project = Project(name="Sample", description="A sample project")
    test_db.add(project)
    await test_db.commit()
    await test_db.refresh(project)
    return project


@pytest.fixture
async def sample_projects(test_db):
    """Create multiple sample projects."""
    from app.models.project import Project

    projects = []
    for i in range(5):
        p = Project(name=f"Project {i}")
        test_db.add(p)
        projects.append(p)
    await test_db.commit()
    for p in projects:
        await test_db.refresh(p)
    return projects
```
