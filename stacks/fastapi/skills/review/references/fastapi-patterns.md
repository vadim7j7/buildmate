# FastAPI Best Practices

Reference patterns for reviewing FastAPI code quality.

---

## Application Factory

```python
from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.config import settings
from app.database import engine
from app.routers import projects, users


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    # Startup
    yield
    # Shutdown
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )

    # Include routers
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")

    return app
```

---

## Dependency Injection

### Database Session

```python
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session with automatic cleanup."""
    async with async_session() as session:
        yield session
```

### Custom Dependencies

```python
from __future__ import annotations

from fastapi import Depends, Query

from app.schemas.pagination import PaginationParams


def get_pagination(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PaginationParams:
    """Parse and validate pagination parameters."""
    return PaginationParams(skip=skip, limit=limit)
```

---

## Error Handling

### Custom Exception Handlers

```python
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    """Resource not found."""

    def __init__(self, resource: str, resource_id: int) -> None:
        self.resource = resource
        self.resource_id = resource_id


class ConflictError(Exception):
    """Resource conflict (e.g., duplicate)."""

    def __init__(self, detail: str) -> None:
        self.detail = detail


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": f"{exc.resource} with id {exc.resource_id} not found"
            },
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": exc.detail},
        )
```

---

## Eager Loading for N+1 Prevention

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.project import Project


async def list_projects_with_tasks(db: AsyncSession) -> list[Project]:
    """List projects with eagerly loaded tasks (prevents N+1)."""
    stmt = (
        select(Project)
        .options(selectinload(Project.tasks))
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
```

---

## Background Task Integration

### FastAPI BackgroundTasks (lightweight)

```python
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

router = APIRouter()


async def send_notification(email: str, message: str) -> None:
    """Send a notification email (background)."""
    # email sending logic
    ...


@router.post("/notify")
async def notify_user(
    email: str, message: str, background_tasks: BackgroundTasks
) -> dict:
    """Queue a notification for background processing."""
    background_tasks.add_task(send_notification, email, message)
    return {"status": "queued"}
```

### Celery Tasks (heavy workloads)

```python
from __future__ import annotations

from fastapi import APIRouter

from app.tasks.sync import sync_external_data

router = APIRouter()


@router.post("/sync/{resource_id}")
async def trigger_sync(resource_id: int) -> dict:
    """Trigger async sync via Celery."""
    sync_external_data.delay(resource_id)
    return {"status": "queued", "resource_id": resource_id}
```

---

## Middleware Patterns

```python
from __future__ import annotations

import time
import logging

from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)


def add_timing_middleware(app: FastAPI) -> None:
    """Add request timing middleware."""

    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        logger.info(
            "Request %s %s completed in %.4fs",
            request.method,
            request.url.path,
            duration,
        )
        return response
```

---

## Review Criteria Summary

| Area | What to Check |
|------|---------------|
| Routers | `response_model`, type annotations, docstrings, status codes |
| Services | Async methods, session injection, error handling |
| Schemas | Pydantic v2 API (`model_dump`, `ConfigDict`), validators |
| Models | `Mapped[]` annotations, relationships, indices |
| Dependencies | `Depends()` injection, no global mutable state |
| Testing | Async tests, fixture isolation, coverage |
| Security | Auth on endpoints, input validation, no raw SQL |
| Performance | N+1 prevention, pagination, background tasks |
