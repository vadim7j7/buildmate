# FastAPI Backend Code Patterns

Reference patterns for FastAPI application development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Router Pattern

Routers define HTTP endpoints using FastAPI's `APIRouter`. Each router handles one
resource type and delegates business logic to a service class.

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectRead]:
    """List all projects with pagination."""
    service = ProjectService(db)
    return await service.list(skip=skip, limit=limit)


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    """Create a new project."""
    service = ProjectService(db)
    return await service.create(payload)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    """Get a single project by ID."""
    service = ProjectService(db)
    project = await service.get_by_id(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    """Update a project by ID (partial update)."""
    service = ProjectService(db)
    project = await service.update(project_id, payload)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a project by ID."""
    service = ProjectService(db)
    deleted = await service.delete(project_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
```

### Router Rules

- Use `APIRouter` with `prefix` and `tags`
- Inject dependencies via `Depends()`
- Use `response_model` for serialization control
- Use appropriate HTTP status codes (201 create, 204 delete)
- Delegate all business logic to service classes
- Add docstrings on all route handlers
- Add type annotations on all parameters and return values
- Handle not-found cases with `HTTPException(404)`

---

## 2. Schema Pattern (Pydantic v2)

Schemas define request/response shapes using Pydantic v2.

```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    """Shared fields for project schemas."""

    name: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""


class ProjectUpdate(BaseModel):
    """Schema for updating a project (all fields optional)."""

    name: str | None = None
    description: str | None = None


class ProjectRead(ProjectBase):
    """Schema for reading a project (includes DB fields)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
```

### Schema Rules

- Base schema holds shared required fields
- Create inherits from Base
- Update has all optional fields (for partial updates)
- Read adds `ConfigDict(from_attributes=True)` for ORM compatibility
- Use `str | None` syntax (not `Optional[str]`)
- Use `list[X]` syntax (not `List[X]`)
- Use `model_dump()` to serialize (never `.dict()`)
- Use `model_validate()` to deserialize (never `.parse_obj()`)
- Add docstrings on all schema classes

---

## 3. Model Pattern (SQLAlchemy 2.0)

Models define database tables using SQLAlchemy 2.0's `Mapped[]` annotations.

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    """SQLAlchemy model for the projects table."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tasks: Mapped[list[Task]] = relationship(back_populates="project")
```

### Model Rules

- Use `Mapped[]` annotations (never legacy `Column()`)
- Use `mapped_column()` for column definitions
- Set `__tablename__` explicitly
- Include `id`, `created_at`, `updated_at` columns
- Use `server_default=func.now()` for timestamps
- Use `String(N)` for varchar, `Text` for unlimited
- Use `ForeignKey()` for foreign key columns
- Use `relationship()` with `back_populates` for bidirectional relationships
- Add composite indices via `__table_args__` for common query patterns

---

## 4. Service Pattern

Services contain business logic and operate on database sessions.

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Business logic for project operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self, *, skip: int = 0, limit: int = 20) -> list[Project]:
        """List projects with pagination."""
        stmt = select(Project).offset(skip).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, project_id: int) -> Project | None:
        """Get a project by primary key."""
        return await self._db.get(Project, project_id)

    async def create(self, payload: ProjectCreate) -> Project:
        """Create a new project."""
        project = Project(**payload.model_dump())
        self._db.add(project)
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def update(
        self, project_id: int, payload: ProjectUpdate
    ) -> Project | None:
        """Update an existing project."""
        project = await self.get_by_id(project_id)
        if project is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def delete(self, project_id: int) -> bool:
        """Delete a project by ID."""
        project = await self.get_by_id(project_id)
        if project is None:
            return False
        await self._db.delete(project)
        await self._db.commit()
        return True
```

### Service Rules

- Inject `AsyncSession` via constructor, store as `self._db`
- All I/O methods are `async`
- Use keyword-only args for optional parameters
- Use `model_dump()` to convert Pydantic schemas
- Use `model_dump(exclude_unset=True)` for partial updates
- Return `None`/`False` for not-found (let router handle HTTP errors)
- Use `selectinload()` for eager loading relationships
- Add docstrings on all public methods

---

## 5. Celery Task Pattern

Tasks handle background work using Celery's `@shared_task` decorator.

```python
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_external_data(self, resource_id: int) -> dict:
    """Sync external data for a resource.

    Args:
        resource_id: The resource ID to sync.

    Returns:
        Status dict with result information.
    """
    logger.info("Starting sync for resource %d", resource_id)
    try:
        # task logic
        return {"status": "ok", "resource_id": resource_id}
    except Exception as exc:
        logger.exception("Sync failed for resource %d", resource_id)
        raise self.retry(exc=exc)
```

### Task Rules

- Use `@shared_task(bind=True)` for `self.retry()` access
- Configure `max_retries` and `default_retry_delay`
- Use `logging` (never `print()`)
- Return a status dict for monitoring
- Catch specific exceptions for retry vs. non-retryable
- Keep tasks small; delegate complex logic to services
- Add Google-style docstrings

---

## 6. Dependency Pattern

Dependencies provide reusable injection points for FastAPI routes.

```python
from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session with automatic cleanup."""
    async with async_session() as session:
        yield session
```

### Dependency Rules

- Use `async def` with `yield` for resource cleanup
- Use `Depends()` in route handler signatures
- Create reusable dependencies for common parameters (pagination, auth)
- Override dependencies in tests with `app.dependency_overrides`

---

## 7. Test Pattern

Tests use pytest with async fixtures and httpx for HTTP testing.

```python
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.schemas.project import ProjectCreate
from app.services.project_service import ProjectService


@pytest.fixture
async def client(test_db: AsyncSession):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestProjectRouter:
    async def test_create_project(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects/", json={"name": "Test"}
        )
        assert response.status_code == 201

    async def test_list_projects(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/projects/")
        assert response.status_code == 200
```

### Test Rules

- Use `async def` for all async tests
- Use `pytest.fixture` for shared setup
- Use `httpx.AsyncClient` with `ASGITransport` for router tests
- Use descriptive class and method names
- One assertion focus per test
- Use `pytest.raises` for expected exceptions
- Use `pytest.mark.parametrize` for multiple inputs
- Isolate tests with per-function database transactions
