# FastAPI Caching Patterns

Caching patterns using Redis for FastAPI.

---

## 1. Redis Setup

```python
# app/core/cache.py
"""Redis cache configuration."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings


class RedisCache:
    """Redis cache client."""

    def __init__(self) -> None:
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self._redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()

    @property
    def client(self) -> redis.Redis:
        """Get Redis client."""
        if not self._redis:
            raise RuntimeError("Redis not connected")
        return self._redis

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: int = 300,
    ) -> None:
        """Set value in cache with expiration."""
        await self.client.setex(key, expire, json.dumps(value))

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        await self.client.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern."""
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)


cache = RedisCache()
```

### Application Lifecycle

```python
# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.cache import cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache.connect()
    yield
    await cache.disconnect()


app = FastAPI(lifespan=lifespan)
```

---

## 2. Cache Dependency

```python
# app/dependencies/cache.py
"""Cache dependency."""

from typing import Annotated

from fastapi import Depends

from app.core.cache import RedisCache, cache


def get_cache() -> RedisCache:
    """Get cache instance."""
    return cache


Cache = Annotated[RedisCache, Depends(get_cache)]
```

---

## 3. Cached Endpoint

```python
# app/api/v1/posts.py
"""Posts with caching."""

from __future__ import annotations

from fastapi import APIRouter

from app.dependencies.cache import Cache
from app.dependencies.database import Database
from app.schemas.post import PostResponse
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    cache: Cache,
    db: Database,
) -> PostResponse:
    """Get post by ID with caching."""
    cache_key = f"posts:{post_id}"

    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return PostResponse(**cached)

    # Fetch from database
    service = PostService(db)
    post = await service.get_by_id(post_id)

    if post:
        # Cache the result
        await cache.set(cache_key, post.model_dump(), expire=300)

    return post
```

---

## 4. Cache Decorator

```python
# app/core/cache.py
"""Caching decorator."""

from __future__ import annotations

import functools
import hashlib
import json
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def cached(
    prefix: str,
    expire: int = 300,
    key_builder: Callable[..., str] | None = None,
) -> Callable[[F], F]:
    """Decorator for caching function results."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key builder
                key_parts = [prefix]
                key_parts.extend(str(arg) for arg in args[1:])  # Skip self
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Try cache
            from app.core.cache import cache

            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                await cache.set(cache_key, result, expire=expire)

            return result

        return wrapper  # type: ignore

    return decorator


# Usage
class PostService:
    @cached(prefix="posts:list", expire=60)
    async def list_posts(self, page: int = 1, per_page: int = 20):
        # This result will be cached
        return await self.db.execute(...)
```

---

## 5. Cache Invalidation

```python
# app/services/post_service.py
"""Post service with cache invalidation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.cache import cache
from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PostService:
    """Post service with caching."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: PostCreate) -> Post:
        """Create post and invalidate list cache."""
        post = Post(**data.model_dump())
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)

        # Invalidate list caches
        await cache.delete_pattern("posts:list:*")

        return post

    async def update(self, post_id: str, data: PostUpdate) -> Post:
        """Update post and invalidate caches."""
        post = await self.get_by_id(post_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(post, key, value)

        await self.db.commit()
        await self.db.refresh(post)

        # Invalidate specific post and list caches
        await cache.delete(f"posts:{post_id}")
        await cache.delete_pattern("posts:list:*")

        return post

    async def delete(self, post_id: str) -> None:
        """Delete post and invalidate caches."""
        post = await self.get_by_id(post_id)
        await self.db.delete(post)
        await self.db.commit()

        # Invalidate caches
        await cache.delete(f"posts:{post_id}")
        await cache.delete_pattern("posts:list:*")
```

---

## 6. Memoization

```python
# app/core/memoize.py
"""In-memory memoization for expensive computations."""

from __future__ import annotations

import functools
from datetime import datetime, timedelta
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class MemoizeCache:
    """Simple in-memory cache with TTL."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[Any, datetime]] = {}

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            value, expires_at = self._cache[key]
            if datetime.now() < expires_at:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        expires_at = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expires_at)

    def clear(self) -> None:
        self._cache.clear()


_memo_cache = MemoizeCache()


def memoize(ttl: int = 60) -> Callable[[F], F]:
    """Decorator for in-memory memoization."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"

            cached = _memo_cache.get(key)
            if cached is not None:
                return cached

            result = await func(*args, **kwargs)
            _memo_cache.set(key, result, ttl)
            return result

        return wrapper  # type: ignore

    return decorator
```

---

## 7. Response Caching Middleware

```python
# app/middleware/cache.py
"""Response caching middleware."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from collections.abc import Callable

from app.core.cache import cache


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """Cache GET responses."""

    def __init__(
        self,
        app,
        cache_paths: list[str] | None = None,
        default_ttl: int = 60,
    ) -> None:
        super().__init__(app)
        self.cache_paths = cache_paths or []
        self.default_ttl = default_ttl

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)

        # Check if path should be cached
        if not self._should_cache(request.url.path):
            return await call_next(request)

        # Build cache key
        cache_key = self._build_cache_key(request)

        # Try cache
        cached = await cache.get(cache_key)
        if cached:
            return Response(
                content=cached["body"],
                status_code=cached["status_code"],
                headers={**cached["headers"], "X-Cache": "HIT"},
                media_type=cached["media_type"],
            )

        # Get response
        response = await call_next(request)

        # Cache successful responses
        if 200 <= response.status_code < 300:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            await cache.set(
                cache_key,
                {
                    "body": body.decode(),
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "media_type": response.media_type,
                },
                expire=self.default_ttl,
            )

            return Response(
                content=body,
                status_code=response.status_code,
                headers={**dict(response.headers), "X-Cache": "MISS"},
                media_type=response.media_type,
            )

        return response

    def _should_cache(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.cache_paths)

    def _build_cache_key(self, request: Request) -> str:
        url_hash = hashlib.md5(str(request.url).encode()).hexdigest()
        return f"response:{url_hash}"
```

---

## 8. Cache Warming

```python
# app/tasks/cache_warmer.py
"""Cache warming tasks."""

from __future__ import annotations

from app.core.cache import cache
from app.core.database import get_db_session
from app.services.post_service import PostService


async def warm_popular_posts_cache() -> int:
    """Pre-populate cache with popular posts."""
    warmed = 0

    async with get_db_session() as db:
        service = PostService(db)
        posts = await service.get_popular(limit=100)

        for post in posts:
            cache_key = f"posts:{post.id}"
            await cache.set(cache_key, post.model_dump(), expire=3600)
            warmed += 1

    return warmed


async def warm_user_profiles_cache() -> int:
    """Pre-populate cache with active user profiles."""
    warmed = 0

    async with get_db_session() as db:
        service = UserService(db)
        users = await service.get_active(limit=1000)

        for user in users:
            cache_key = f"users:{user.id}"
            await cache.set(cache_key, user.model_dump(), expire=1800)
            warmed += 1

    return warmed
```

---

## 9. Cache Health Check

```python
# app/api/health.py
"""Health check endpoints."""

from fastapi import APIRouter

from app.core.cache import cache

router = APIRouter(tags=["health"])


@router.get("/health/cache")
async def cache_health() -> dict:
    """Check cache health."""
    try:
        # Test set and get
        test_key = "health:check"
        await cache.set(test_key, {"status": "ok"}, expire=10)
        result = await cache.get(test_key)
        await cache.delete(test_key)

        if result and result.get("status") == "ok":
            return {"status": "healthy", "message": "Cache is working"}

        return {"status": "unhealthy", "message": "Cache read/write failed"}

    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}
```

---

## 10. Testing Cache

```python
# tests/test_cache.py
"""Cache tests."""

from __future__ import annotations

import pytest

from app.core.cache import cache


@pytest.fixture
async def redis_cache():
    """Setup cache for tests."""
    await cache.connect()
    yield cache
    await cache.delete_pattern("test:*")
    await cache.disconnect()


@pytest.mark.asyncio
async def test_cache_set_get(redis_cache) -> None:
    """Test cache set and get."""
    await redis_cache.set("test:key", {"data": "value"}, expire=60)
    result = await redis_cache.get("test:key")

    assert result == {"data": "value"}


@pytest.mark.asyncio
async def test_cache_delete(redis_cache) -> None:
    """Test cache delete."""
    await redis_cache.set("test:delete", {"data": "value"}, expire=60)
    await redis_cache.delete("test:delete")
    result = await redis_cache.get("test:delete")

    assert result is None


@pytest.mark.asyncio
async def test_cache_pattern_delete(redis_cache) -> None:
    """Test cache pattern delete."""
    await redis_cache.set("test:pattern:1", {"data": "1"}, expire=60)
    await redis_cache.set("test:pattern:2", {"data": "2"}, expire=60)
    await redis_cache.set("test:other:1", {"data": "3"}, expire=60)

    await redis_cache.delete_pattern("test:pattern:*")

    assert await redis_cache.get("test:pattern:1") is None
    assert await redis_cache.get("test:pattern:2") is None
    assert await redis_cache.get("test:other:1") is not None


@pytest.mark.asyncio
async def test_cached_endpoint(client, redis_cache) -> None:
    """Test endpoint caching."""
    # First request - cache miss
    response1 = await client.get("/api/v1/posts/1")
    assert response1.status_code == 200

    # Second request - cache hit (verify via X-Cache header if implemented)
    response2 = await client.get("/api/v1/posts/1")
    assert response2.status_code == 200
```
