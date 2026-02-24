# FastAPI Rate Limiting Patterns

Rate limiting patterns using SlowAPI and Redis.

---

## 1. SlowAPI Setup

### Installation

```bash
pip install slowapi redis
```

### Basic Configuration

```python
# app/core/limiter.py
"""Rate limiter configuration."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

### Application Setup

```python
# app/main.py
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.limiter import limiter

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

---

## 2. Basic Rate Limiting

```python
# app/api/v1/posts.py
"""Posts with rate limiting."""

from fastapi import APIRouter, Request

from app.core.limiter import limiter

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("")
@limiter.limit("100/minute")
async def list_posts(request: Request):
    """List posts - 100 requests per minute."""
    return {"posts": []}


@router.post("")
@limiter.limit("10/minute")
async def create_post(request: Request):
    """Create post - 10 requests per minute."""
    return {"id": 1}
```

---

## 3. User-Based Rate Limiting

```python
# app/core/limiter.py
"""Rate limiter with user identification."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slowapi import Limiter
from slowapi.util import get_remote_address

if TYPE_CHECKING:
    from fastapi import Request


def get_user_identifier(request: Request) -> str:
    """Get rate limit key based on user or IP."""
    # Try to get user from auth
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=get_user_identifier)
```

---

## 4. Redis Backend

```python
# app/core/limiter.py
"""Rate limiter with Redis storage."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def get_user_identifier(request) -> str:
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=get_user_identifier,
    storage_uri=settings.REDIS_URL,
    strategy="fixed-window",  # or "moving-window"
)
```

---

## 5. Custom Rate Limit Responses

```python
# app/core/limiter.py
"""Custom rate limit error handling."""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded


async def custom_rate_limit_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """Custom rate limit exceeded response."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded: {exc.detail}",
            "retry_after": exc.retry_after,
        },
        headers={
            "Retry-After": str(exc.retry_after),
            "X-RateLimit-Limit": request.state.view_rate_limit,
            "X-RateLimit-Remaining": "0",
        },
    )


# In main.py
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
```

---

## 6. Tiered Rate Limits

```python
# app/dependencies/rate_limit.py
"""Tiered rate limiting based on user plan."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.dependencies.auth import get_current_user
from app.models.user import User

RATE_LIMITS = {
    "free": {"requests": 100, "window": "hour"},
    "pro": {"requests": 1000, "window": "hour"},
    "enterprise": {"requests": 10000, "window": "hour"},
}


async def check_rate_limit(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Check rate limit based on user's plan."""
    plan = user.subscription_plan or "free"
    limits = RATE_LIMITS.get(plan, RATE_LIMITS["free"])

    # Get current count from Redis
    redis = request.app.state.redis
    key = f"ratelimit:{user.id}:{limits['window']}"

    current = await redis.incr(key)
    if current == 1:
        # Set expiry on first request
        ttl = 3600 if limits["window"] == "hour" else 60
        await redis.expire(key, ttl)

    if current > limits["requests"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {limits['requests']}/{limits['window']}",
            headers={"Retry-After": str(await redis.ttl(key))},
        )

    # Set rate limit headers
    request.state.rate_limit_limit = limits["requests"]
    request.state.rate_limit_remaining = max(0, limits["requests"] - current)


RateLimited = Annotated[None, Depends(check_rate_limit)]
```

---

## 7. Endpoint-Specific Limits

```python
# app/api/v1/auth.py
"""Auth endpoints with specific rate limits."""

from fastapi import APIRouter, Request

from app.core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
@limiter.limit("5/minute")  # Strict limit for login
async def login(request: Request):
    """Login - 5 attempts per minute."""
    pass


@router.post("/register")
@limiter.limit("3/hour")  # Very strict for registration
async def register(request: Request):
    """Register - 3 attempts per hour."""
    pass


@router.post("/forgot-password")
@limiter.limit("3/hour")
async def forgot_password(request: Request):
    """Password reset - 3 requests per hour."""
    pass
```

---

## 8. Rate Limit Middleware

```python
# app/middleware/rate_limit.py
"""Rate limiting middleware."""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from collections.abc import Callable

import redis.asyncio as redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for global rate limiting."""

    def __init__(
        self,
        app,
        redis_url: str,
        requests_per_minute: int = 60,
    ) -> None:
        super().__init__(app)
        self.redis = redis.from_url(redis_url)
        self.requests_per_minute = requests_per_minute

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Skip rate limiting for certain paths
        if request.url.path.startswith("/health"):
            return await call_next(request)

        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        key = f"global_ratelimit:{client_ip}"

        # Check and increment
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, 60)

        # Get remaining
        remaining = max(0, self.requests_per_minute - current)
        ttl = await self.redis.ttl(key)

        if current > self.requests_per_minute:
            return Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=429,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": str(ttl),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(ttl),
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(ttl)

        return response
```

---

## 9. Sliding Window Rate Limiter

```python
# app/services/rate_limiter.py
"""Sliding window rate limiter using Redis sorted sets."""

from __future__ import annotations

import time
from dataclasses import dataclass

import redis.asyncio as redis


@dataclass
class RateLimitResult:
    """Rate limit check result."""

    allowed: bool
    limit: int
    remaining: int
    reset_at: float


class SlidingWindowRateLimiter:
    """Sliding window rate limiter using Redis sorted sets."""

    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis = redis_client

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Check if request is allowed."""
        now = time.time()
        window_start = now - window_seconds

        pipe = self.redis.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current entries
        pipe.zcard(key)

        # Add new entry
        pipe.zadd(key, {str(now): now})

        # Set expiry
        pipe.expire(key, window_seconds)

        results = await pipe.execute()
        current_count = results[1]

        allowed = current_count < limit
        remaining = max(0, limit - current_count - 1) if allowed else 0

        # Get oldest entry to calculate reset time
        oldest = await self.redis.zrange(key, 0, 0, withscores=True)
        reset_at = oldest[0][1] + window_seconds if oldest else now + window_seconds

        return RateLimitResult(
            allowed=allowed,
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
        )
```

---

## 10. Testing Rate Limits

```python
# tests/test_rate_limit.py
"""Rate limiting tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rate_limit_not_exceeded(client: AsyncClient) -> None:
    """Test normal request within rate limit."""
    response = await client.get("/api/v1/posts")

    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers


@pytest.mark.asyncio
async def test_rate_limit_exceeded(client: AsyncClient) -> None:
    """Test rate limit exceeded."""
    # Make requests until limit exceeded
    for i in range(101):
        response = await client.get("/api/v1/posts")
        if response.status_code == 429:
            break

    assert response.status_code == 429
    assert "Retry-After" in response.headers
    data = response.json()
    assert data["error"] == "rate_limit_exceeded"


@pytest.mark.asyncio
async def test_login_rate_limit(client: AsyncClient) -> None:
    """Test strict rate limit on login."""
    for i in range(6):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "wrong"},
        )

    # 6th request should be rate limited
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_rate_limit_headers(client: AsyncClient) -> None:
    """Test rate limit headers are present."""
    response = await client.get("/api/v1/posts")

    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

    limit = int(response.headers["X-RateLimit-Limit"])
    remaining = int(response.headers["X-RateLimit-Remaining"])

    assert remaining < limit
```
