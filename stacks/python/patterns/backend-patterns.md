# Python Backend Code Patterns

Reference patterns for Python application development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Schema Pattern (Pydantic v2)

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

## 2. Model Pattern (SQLAlchemy 2.0)

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

## 3. Service Pattern

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
- Return `None`/`False` for not-found (let caller handle errors)
- Use `selectinload()` for eager loading relationships
- Add docstrings on all public methods

---

## 4. Migration Pattern (Alembic)

Migrations use Alembic with async engine support.

```python
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    """Create the projects table."""
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Drop the projects table."""
    op.drop_table("projects")
```

### Migration Rules

- Always include `upgrade()` and `downgrade()`
- Use descriptive docstrings
- Keep migrations atomic (one logical change per migration)
- Test both upgrade and downgrade
- Use `op.create_index()` for new indices

---

## 5. Test Patterns

Tests use pytest with async fixtures.

### Service Tests (Unit)

```python
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.project import ProjectCreate
from app.services.project_service import ProjectService


class TestProjectService:
    """Tests for ProjectService business logic."""

    async def test_create_project(self, test_db: AsyncSession) -> None:
        service = ProjectService(test_db)
        payload = ProjectCreate(name="Test", description="A test project")
        project = await service.create(payload)

        assert project.id is not None
        assert project.name == "Test"

    async def test_get_by_id_returns_none_for_missing(
        self, test_db: AsyncSession
    ) -> None:
        service = ProjectService(test_db)
        result = await service.get_by_id(99999)
        assert result is None
```

### Schema Tests

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.project import ProjectCreate


class TestProjectSchemas:
    """Tests for Pydantic schema validation."""

    def test_create_schema_valid(self) -> None:
        schema = ProjectCreate(name="Test")
        assert schema.name == "Test"

    def test_create_schema_requires_name(self) -> None:
        with pytest.raises(ValidationError):
            ProjectCreate()
```

### Test Rules

- Use `async def` for all async tests
- Use `pytest.fixture` for shared setup
- Use descriptive class and method names
- One assertion focus per test
- Use `pytest.raises` for expected exceptions
- Use `pytest.mark.parametrize` for multiple inputs
- Isolate tests with per-function database transactions

---

## 6. Error Handling Pattern

```python
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Base exception for service-layer errors."""


class NotFoundError(ServiceError):
    """Raised when a requested resource does not exist."""


class ConflictError(ServiceError):
    """Raised on duplicate or conflicting state."""
```

### Error Handling Rules

- Define domain exceptions inheriting from a base `ServiceError`
- Catch specific exceptions (never bare `except`)
- Use `logging.exception()` in except blocks
- Let callers (routes, CLI) translate domain errors to HTTP/exit codes

---

## 7. Logging Pattern

```python
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MyService:
    async def process(self, item_id: int) -> None:
        logger.info("Processing item %d", item_id)
        try:
            # ...
            logger.info("Item %d processed successfully", item_id)
        except ValueError:
            logger.exception("Failed to process item %d", item_id)
```

### Logging Rules

- Use `logging.getLogger(__name__)` at module level
- Use `%`-style formatting in log calls (lazy evaluation)
- Use `logger.exception()` in except blocks (includes traceback)
- Never log sensitive data (passwords, tokens, PII)
