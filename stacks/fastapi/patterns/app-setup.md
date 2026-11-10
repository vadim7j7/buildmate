# FastAPI App Setup: Settings, Lifespan, DB Session, CLI

Read when creating the app, adding a setting or env var, adding something that
starts/stops with the app (DB engine, HTTP client, cache), or changing how the
server runs. MongoDB projects: the engine/session parts are replaced by
`init_beanie` in the lifespan (`mongodb.md`); settings and CLI are the same.

## Settings: pydantic-settings

Dependency: `pydantic-settings`.

```python
# src/app/config.py
from functools import lru_cache

from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings, read once from the environment (and .env locally)."""

    model_config = SettingsConfigDict(
        env_file=".env",            # local only; real env vars win over it
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    debug: bool = False
    database_url: PostgresDsn       # DATABASE_URL; required, no default
    secret_key: SecretStr           # SECRET_KEY; str(settings.secret_key) shows ****
    cors_origins: list[str] = []    # CORS_ORIGINS='["https://app.example.com"]'
    db_pool_size: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

Rules:
- Field names map to env vars case-insensitively (`database_url` <- `DATABASE_URL`);
  use `env_prefix="APP_"` if names collide with other tools.
- Secrets are `SecretStr` (call `.get_secret_value()` where needed); no defaults.
- A missing or invalid variable fails at startup with a clear validation error.
- Every new variable goes into `.env.example`.
- Tests override with env vars (`monkeypatch.setenv` before `get_settings.cache_clear()`)
  or by overriding the `get_settings` dependency.

## Lifespan: Startup and Shutdown

`@app.on_event("startup")` is deprecated; use one `lifespan` context manager.

```python
# src/app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.config import settings
from app.db import engine
from app.routers import projects


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: create shared, long-lived resources once
    app.state.http = httpx.AsyncClient(timeout=10)
    yield
    # Shutdown: release them (runs on SIGTERM too)
    await app.state.http.aclose()
    await engine.dispose()


app = FastAPI(title="API", lifespan=lifespan, debug=settings.debug)
app.include_router(projects.router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

Do not open connections at import time (module level): it breaks tests and the
CLI's reload process.

## Database Session per Request

One engine per process (module level is fine: it connects lazily); one session
per request, provided by a `yield` dependency.

```python
# src/app/db.py
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    str(settings.database_url),   # postgresql+asyncpg://...
    pool_size=settings.db_pool_size,
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """One session per request; rolled back if the handler raises."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]
```

```python
# src/app/routers/projects.py
@router.post("/", status_code=201)
async def create_project(payload: ProjectCreate, db: DbSession) -> ProjectRead:
    return await ProjectService(db).create(payload)   # the service commits
```

Rules:
- `Annotated[..., Depends(...)]` aliases (`DbSession`, `CurrentUser`) instead of
  repeating `= Depends(get_db)` in every signature.
- FastAPI caches a dependency per request: two dependencies that both ask for
  `DbSession` get the same session.
- `expire_on_commit=False`, so returning an ORM object after commit does not
  trigger lazy loads (which fail in async).
- Background work (`BackgroundTasks`, Celery) opens its own session with
  `async with SessionLocal() as session:`; never pass the request's session on.
- Tests override the dependency: `app.dependency_overrides[get_db] = override`
  with a session bound to a transaction that is rolled back after each test.

## Running: the `fastapi` CLI

With `fastapi[standard]` installed (it brings `fastapi-cli` and uvicorn):

```bash
uv run fastapi dev src/app/main.py --port 8000   # auto-reload, binds 127.0.0.1
uv run fastapi run src/app/main.py --port 8000   # production: no reload, binds 0.0.0.0
uv run fastapi run src/app/main.py --workers 4   # several processes
```

The plain uvicorn equivalent (what this stack's verification uses, and what
works with only `uvicorn` installed):

```bash
uv run uvicorn app.main:app --reload --port 8000
```

In containers run `fastapi run` (or `uvicorn` without `--reload`) and put a
proxy that sets `X-Forwarded-*` in front; pass `--proxy-headers` /
`--forwarded-allow-ips` when the app needs the client's scheme or IP.
