# Python FastAPI Agent System

This project uses a multi-agent architecture powered by Claude Code, specialised for
Python FastAPI backends. A single main agent orchestrates work by delegating to
specialised sub-agents through the **Task** tool. Sub-agents never spawn their own
sub-agents; only the main agent delegates.

## Quick Start

Say **"Use PM: [task description]"** in any conversation to trigger the full
orchestration pipeline. The PM agent will break the task down, create a feature file,
and drive the pipeline to completion.

## Project Structure

```
src/
  app/
    main.py              # FastAPI app factory, lifespan, middleware
    config.py            # Pydantic Settings (env vars)
    database.py          # async engine + sessionmaker + get_db dependency
    routers/             # FastAPI APIRouter modules
    schemas/             # Pydantic v2 request/response models
    models/              # SQLAlchemy 2.0 ORM models (Mapped[])
    services/            # Business logic classes (async)
    tasks/               # Celery task modules
    dependencies/        # Shared FastAPI Depends() callables
    exceptions/          # Custom exception classes + handlers
    middleware/           # Custom middleware
tests/
  conftest.py            # Fixtures: async client, test db session
  routers/               # Router integration tests
  services/              # Service unit tests
  tasks/                 # Task unit tests
alembic/
  env.py                 # Alembic async env
  versions/              # Migration files
alembic.ini
pyproject.toml           # uv project config, ruff, mypy, pytest settings
```

## Key Commands

| Command                                    | Purpose                              |
|--------------------------------------------|--------------------------------------|
| `uv run pytest`                            | Run the full test suite              |
| `uv run pytest tests/path`                 | Run a specific test file or dir      |
| `uv run ruff check src/ tests/`            | Lint all Python files                |
| `uv run ruff format src/ tests/`           | Format all Python files              |
| `uv run ruff check --fix src/ tests/`      | Auto-fix lint violations             |
| `uv run mypy src/`                         | Run type checking                    |
| `uv run alembic upgrade head`              | Run pending database migrations      |
| `uv run alembic downgrade -1`              | Roll back the last migration         |
| `uv run alembic revision --autogenerate -m "msg"` | Generate a new migration      |
| `uv run python -m app.main`               | Run the development server           |
| `uv add <package>`                         | Add a dependency                     |
| `uv sync`                                  | Sync dependencies from lockfile      |

## Agent Pipeline

Every non-trivial task flows through the following stages:

```
Plan --> Implement --> Test --> Review --> Eval --> Security
```

| Stage      | Agent              | Purpose                                    |
|------------|--------------------|--------------------------------------------|
| Plan       | PM (orchestrator)  | Break task into sub-tasks, create feature  |
| Implement  | backend-developer  | Write production FastAPI code              |
| Test       | backend-tester     | Write and run pytest tests                 |
| Review     | backend-reviewer   | Code review against Python/FastAPI conventions |
| Eval       | eval-agent         | Score against quality rubrics              |
| Security   | security-auditor   | OWASP scan, vulnerability check            |

## Code Patterns

### Router Pattern

Routers use FastAPI's `APIRouter`, dependency injection, and type annotations.

```python
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
    service = ProjectService(db)
    return await service.list(skip=skip, limit=limit)

@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    service = ProjectService(db)
    return await service.create(payload)
```

### Schema Pattern (Pydantic v2)

Schemas use Pydantic v2 with `model_config = ConfigDict(from_attributes=True)` for
ORM integration.

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ProjectBase(BaseModel):
    name: str
    description: str | None = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
```

### Model Pattern (SQLAlchemy 2.0)

Models use the SQLAlchemy 2.0 `Mapped[]` annotation style.

```python
from datetime import datetime
from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
```

### Service Pattern

Services are async classes injected with a database session.

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

class ProjectService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self, *, skip: int = 0, limit: int = 20) -> list[Project]:
        stmt = select(Project).offset(skip).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, project_id: int) -> Project | None:
        return await self._db.get(Project, project_id)

    async def create(self, payload: ProjectCreate) -> Project:
        project = Project(**payload.model_dump())
        self._db.add(project)
        await self._db.commit()
        await self._db.refresh(project)
        return project
```

### Celery Task Pattern

Tasks use the `@shared_task` decorator with retry configuration.

```python
from celery import shared_task

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_external_data(self, resource_id: int) -> dict:
    try:
        # task logic
        return {"status": "ok", "resource_id": resource_id}
    except Exception as exc:
        raise self.retry(exc=exc)
```

## Python Style Rules

- **PEP 8** enforced by Ruff
- **Type annotations** on all function signatures (enforced by mypy strict mode)
- **Docstrings** on all public classes and functions (Google-style)
- **`from __future__ import annotations`** at the top of every module for PEP 604 unions
- **f-strings** for string formatting (never `%` or `.format()`)
- **`snake_case`** for functions, methods, variables; **`PascalCase`** for classes
- **`SCREAMING_SNAKE_CASE`** for constants
- Prefer `|` union syntax: `str | None` over `Optional[str]`
- Use `Mapped[]` annotations for SQLAlchemy models (never legacy `Column()`)
- Use `model_dump()` / `model_validate()` (never deprecated `.dict()` / `.parse_obj()`)
- Prefer `list[X]`, `dict[K, V]` over `typing.List`, `typing.Dict`
- Line length max 88 (Ruff default)
- Import order: stdlib, third-party, local (enforced by Ruff isort)

## Quality Gates

Before the review stage, the following gates **must** pass:

| Gate     | Command                                  | Requirement        |
|----------|------------------------------------------|--------------------|
| Format   | `uv run ruff format --check src/ tests/` | Zero reformats     |
| Lint     | `uv run ruff check src/ tests/`          | Zero violations    |
| Types    | `uv run mypy src/`                       | Zero errors        |
| Tests    | `uv run pytest`                          | All passing        |

If any gate fails, the implementing agent must fix the issues before proceeding.

## Feature Tracking

Features are tracked as markdown files in `.claude/context/features/`.

```bash
# Convention: YYYYMMDD-short-slug.md
touch .claude/context/features/20260201-user-auth.md
```

## Available Slash Commands

| Command           | Description                                          |
|-------------------|------------------------------------------------------|
| `/test`           | Run pytest tests via backend-tester agent            |
| `/review`         | Code review via backend-reviewer agent               |
| `/db-migrate`     | Create and run Alembic migrations safely             |
| `/new-router`     | Generate a FastAPI router with CRUD endpoints        |
| `/new-schema`     | Generate a Pydantic v2 schema set                    |
| `/new-model`      | Generate a SQLAlchemy 2.0 model                      |
| `/new-service`    | Generate an async service class                      |
| `/new-migration`  | Generate an Alembic migration                        |
| `/new-test`       | Generate a pytest test file                          |
| `/new-task`       | Generate a Celery task                               |

## Delegation Rules

1. **Only the main agent delegates.** Sub-agents receive a task, execute it,
   and return results. They never call the Task tool themselves.
2. **One responsibility per agent.** Each sub-agent owns a single concern
   (implementing, testing, reviewing).
3. **Context flows forward.** Each stage writes its output to
   `.agent-pipeline/<stage>.md` so the next stage can read it.
4. **Failures stop the pipeline.** If a stage fails, the pipeline halts and
   the main agent reports the failure with actionable details.
