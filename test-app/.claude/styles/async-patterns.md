# FastAPI Async Patterns Style Guide

Best practices for async/await patterns in FastAPI applications.

---

## Async Fundamentals

### Basic Async Endpoints

```python
# app/api/v1/users.py
"""Async endpoint examples."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


# Always use async for I/O operations
@router.get("/{user_id}")
async def get_user(user_id: str):
    """Async endpoint - preferred for I/O bound operations."""
    user = await db.users.find_one(user_id)
    return user


# Sync is fine for CPU-bound or no I/O
@router.get("/count")
def get_user_count():
    """Sync endpoint - OK for simple operations."""
    return {"count": 100}
```

---

## Database Operations

### Async SQLAlchemy

```python
# app/core/database.py
"""Async database configuration."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings

# Use async driver
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency for getting database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

### Repository Pattern

```python
# app/repositories/user_repository.py
"""Async repository pattern."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    """Async user repository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_with_orders(self, user_id: str) -> User | None:
        """Get user with orders loaded."""
        result = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.orders))
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Get all users with pagination."""
        result = await self.session.execute(
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, **data) -> User:
        """Create a new user."""
        user = User(**data)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user: User, **data) -> User:
        """Update user."""
        for key, value in data.items():
            setattr(user, key, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Delete user."""
        await self.session.delete(user)
        await self.session.commit()
```

---

## Concurrent Operations

### Gather for Parallel Calls

```python
# app/services/dashboard_service.py
"""Concurrent data fetching."""

from __future__ import annotations

import asyncio
from typing import Any


class DashboardService:
    """Service for dashboard data."""

    async def get_dashboard_data(self, user_id: str) -> dict[str, Any]:
        """Fetch all dashboard data concurrently."""
        # Run independent queries in parallel
        user, orders, notifications, analytics = await asyncio.gather(
            self.get_user(user_id),
            self.get_recent_orders(user_id),
            self.get_notifications(user_id),
            self.get_analytics(user_id),
        )

        return {
            "user": user,
            "orders": orders,
            "notifications": notifications,
            "analytics": analytics,
        }

    async def get_user(self, user_id: str) -> dict:
        # Fetch user
        pass

    async def get_recent_orders(self, user_id: str) -> list:
        # Fetch orders
        pass

    async def get_notifications(self, user_id: str) -> list:
        # Fetch notifications
        pass

    async def get_analytics(self, user_id: str) -> dict:
        # Fetch analytics
        pass
```

### Error Handling with gather

```python
# app/services/batch_service.py
"""Batch operations with error handling."""

from __future__ import annotations

import asyncio
from typing import Any


async def process_batch_with_errors(
    items: list[str],
) -> tuple[list[Any], list[Exception]]:
    """Process batch, collecting both results and errors."""
    results = await asyncio.gather(
        *[process_item(item) for item in items],
        return_exceptions=True,
    )

    successes = []
    errors = []

    for result in results:
        if isinstance(result, Exception):
            errors.append(result)
        else:
            successes.append(result)

    return successes, errors


async def process_item(item: str) -> dict:
    """Process a single item."""
    # Implementation
    pass
```

### TaskGroup for Structured Concurrency (Python 3.11+)

```python
# app/services/task_service.py
"""Using TaskGroup for structured concurrency."""

from __future__ import annotations

import asyncio
from typing import Any


async def fetch_all_resources(resource_ids: list[str]) -> list[dict]:
    """Fetch resources using TaskGroup."""
    results = []

    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(fetch_resource(rid))
            for rid in resource_ids
        ]

    # All tasks completed successfully if we reach here
    results = [task.result() for task in tasks]
    return results


async def fetch_resource(resource_id: str) -> dict:
    """Fetch a single resource."""
    # Implementation
    pass
```

---

## Semaphores for Rate Limiting

```python
# app/services/external_api.py
"""Rate-limited external API calls."""

from __future__ import annotations

import asyncio

import httpx


class ExternalAPIClient:
    """Client with rate limiting."""

    def __init__(self, max_concurrent: int = 10) -> None:
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.client = httpx.AsyncClient()

    async def fetch(self, url: str) -> dict:
        """Fetch with rate limiting."""
        async with self.semaphore:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()

    async def fetch_many(self, urls: list[str]) -> list[dict]:
        """Fetch multiple URLs with rate limiting."""
        return await asyncio.gather(
            *[self.fetch(url) for url in urls]
        )

    async def close(self) -> None:
        """Close the client."""
        await self.client.aclose()
```

---

## Timeouts

```python
# app/services/timeout_service.py
"""Timeout patterns."""

from __future__ import annotations

import asyncio

from app.core.errors import TimeoutError


async def with_timeout(
    coro,
    timeout: float,
    error_message: str = "Operation timed out",
):
    """Execute coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(error_message)


# Usage
async def fetch_with_timeout(url: str) -> dict:
    """Fetch URL with 5 second timeout."""
    return await with_timeout(
        fetch_url(url),
        timeout=5.0,
        error_message=f"Request to {url} timed out",
    )
```

---

## Background Tasks

### FastAPI Background Tasks

```python
# app/api/v1/orders.py
"""Background task patterns."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

from app.services.email_service import send_order_confirmation
from app.services.analytics_service import track_order

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("")
async def create_order(
    data: OrderCreate,
    background_tasks: BackgroundTasks,
):
    """Create order with background processing."""
    order = await order_service.create(data)

    # Schedule background tasks
    background_tasks.add_task(send_order_confirmation, order.id)
    background_tasks.add_task(track_order, order.id)

    return order
```

### Long-Running Tasks with asyncio.create_task

```python
# app/services/processor.py
"""Long-running background processing."""

from __future__ import annotations

import asyncio
from typing import Any


class BackgroundProcessor:
    """Background task processor."""

    def __init__(self) -> None:
        self.tasks: set[asyncio.Task] = set()

    def schedule(self, coro) -> asyncio.Task:
        """Schedule a background task."""
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    async def shutdown(self) -> None:
        """Cancel all pending tasks."""
        for task in self.tasks:
            task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)


# Global processor
processor = BackgroundProcessor()


# Usage in service
async def process_upload(file_id: str) -> None:
    """Schedule file processing in background."""
    processor.schedule(process_file_async(file_id))


async def process_file_async(file_id: str) -> None:
    """Process file asynchronously."""
    # Long-running operation
    pass
```

---

## Async Context Managers

```python
# app/core/resources.py
"""Async context manager patterns."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx


@asynccontextmanager
async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async context manager for HTTP client."""
    client = httpx.AsyncClient(timeout=30.0)
    try:
        yield client
    finally:
        await client.aclose()


# Usage
async def fetch_data(url: str) -> dict:
    async with get_http_client() as client:
        response = await client.get(url)
        return response.json()


# Reusable client pool
class HTTPClientPool:
    """Pool of HTTP clients."""

    def __init__(self, pool_size: int = 10) -> None:
        self.pool_size = pool_size
        self.clients: list[httpx.AsyncClient] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> httpx.AsyncClient:
        """Acquire a client from the pool."""
        async with self._lock:
            if self.clients:
                return self.clients.pop()

            if len(self.clients) < self.pool_size:
                return httpx.AsyncClient()

        # Wait for available client
        await asyncio.sleep(0.1)
        return await self.acquire()

    async def release(self, client: httpx.AsyncClient) -> None:
        """Return client to pool."""
        async with self._lock:
            self.clients.append(client)

    @asynccontextmanager
    async def get(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Context manager for pool access."""
        client = await self.acquire()
        try:
            yield client
        finally:
            await self.release(client)
```

---

## Async Generators

```python
# app/services/streaming.py
"""Async generator patterns."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()


async def generate_report_data(report_id: str) -> AsyncGenerator[bytes, None]:
    """Generate report data as async stream."""
    async for chunk in fetch_report_chunks(report_id):
        yield chunk


@router.get("/reports/{report_id}/download")
async def download_report(report_id: str):
    """Stream report download."""
    return StreamingResponse(
        generate_report_data(report_id),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=report-{report_id}.csv"
        },
    )


# Paginated async iteration
async def iter_all_users() -> AsyncGenerator[User, None]:
    """Iterate all users in batches."""
    offset = 0
    batch_size = 100

    while True:
        users = await user_repo.get_all(skip=offset, limit=batch_size)
        if not users:
            break

        for user in users:
            yield user

        offset += batch_size
```

---

## Best Practices

1. **Always use async for I/O** - Database, HTTP, file operations
2. **Use gather for parallel work** - Independent operations
3. **Handle timeouts** - Prevent hanging operations
4. **Use semaphores for rate limiting** - Control concurrency
5. **Prefer TaskGroup (3.11+)** - Structured concurrency with proper cancellation
6. **Don't block the event loop** - Use `run_in_executor` for sync code
7. **Clean up resources** - Use async context managers
8. **Handle exceptions properly** - Use `return_exceptions` when appropriate

```python
# Running sync code in async context
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)


async def run_sync_in_thread(sync_func, *args):
    """Run synchronous function in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, sync_func, *args)


# Usage
async def process_image(image_data: bytes) -> bytes:
    """Process image using sync library."""
    return await run_sync_in_thread(
        sync_image_processor.process,
        image_data,
    )
```
