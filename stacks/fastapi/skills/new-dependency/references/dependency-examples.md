# FastAPI Dependency Examples

Reference examples for generating dependency injection functions.

## Database Session Dependency

```python
"""Database session dependency."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, AsyncGenerator

from fastapi import Depends

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for the request.

    Yields:
        AsyncSession that will be closed after the request.

    Example:
        @router.get("/users")
        async def list_users(
            db: Annotated[AsyncSession, Depends(get_db)],
        ) -> list[User]:
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Type alias for cleaner signatures
Database = Annotated[AsyncSession, Depends(get_db)]
```

## Settings Dependency

```python
"""Settings dependency with caching."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment."""

    app_name: str = "MyApp"
    debug: bool = False
    database_url: str
    redis_url: str | None = None
    secret_key: str
    allowed_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Cached Settings instance.

    Example:
        @router.get("/info")
        async def get_info(
            settings: Annotated[Settings, Depends(get_settings)],
        ) -> dict[str, str]:
            return {"app_name": settings.app_name}
    """
    return Settings()


# Type alias for cleaner signatures
AppSettings = Annotated[Settings, Depends(get_settings)]
```

## Pagination Dependency

```python
"""Pagination dependency for list endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Query


@dataclass(frozen=True, slots=True)
class PaginationParams:
    """Pagination parameters for list queries.

    Attributes:
        offset: Number of records to skip.
        limit: Maximum number of records to return.
    """

    offset: int
    limit: int

    @property
    def page(self) -> int:
        """Calculate the current page number (1-indexed)."""
        return (self.offset // self.limit) + 1


def get_pagination(
    offset: Annotated[int, Query(ge=0, description="Records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max records")] = 20,
) -> PaginationParams:
    """Extract pagination parameters from query string.

    Args:
        offset: Number of records to skip (default: 0).
        limit: Maximum records to return (default: 20, max: 100).

    Returns:
        PaginationParams with validated offset and limit.

    Example:
        @router.get("/items")
        async def list_items(
            pagination: Pagination,
        ) -> list[Item]:
            return await service.list(
                offset=pagination.offset,
                limit=pagination.limit,
            )
    """
    return PaginationParams(offset=offset, limit=limit)


# Type alias for cleaner signatures
Pagination = Annotated[PaginationParams, Depends(get_pagination)]
```

## Authentication Dependency

```python
"""Authentication dependencies for protected routes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

if TYPE_CHECKING:
    from app.models.user import User

from app.services.auth_service import AuthService, get_auth_service

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """Extract and validate the current user from JWT token.

    Args:
        credentials: Bearer token from Authorization header.
        auth_service: Authentication service for token validation.

    Returns:
        The authenticated User.

    Raises:
        HTTPException: 401 if token is invalid or expired.

    Example:
        @router.get("/profile")
        async def get_profile(user: CurrentUser) -> UserProfile:
            return UserProfile.from_user(user)
    """
    try:
        user = await auth_service.validate_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))
    ],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User | None:
    """Optionally extract user, returning None if unauthenticated.

    Example:
        @router.get("/posts")
        async def list_posts(user: OptionalUser) -> list[Post]:
            if user:
                return await get_posts_for_user(user)
            return await get_public_posts()
    """
    if credentials is None:
        return None

    try:
        return await auth_service.validate_token(credentials.credentials)
    except ValueError:
        return None


# Type aliases for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
```

## Admin Only Dependency

```python
"""Admin authorization dependency."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.dependencies.auth import CurrentUser
from app.models.user import User


async def get_admin_user(user: CurrentUser) -> User:
    """Require admin role for the current user.

    Args:
        user: The authenticated user.

    Returns:
        The user if they are an admin.

    Raises:
        HTTPException: 403 if user is not an admin.

    Example:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: int,
            admin: AdminUser,
        ) -> None:
            await user_service.delete(user_id)
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


AdminUser = Annotated[User, Depends(get_admin_user)]
```

## Service Dependency (Class-Based)

```python
"""Service dependencies with class-based injection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import Database


class UserService:
    """User service with injected database session."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            db: Database session for queries.
        """
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> list[User]:
        """List users with pagination."""
        result = await self.db.execute(
            select(User).offset(offset).limit(limit)
        )
        return list(result.scalars().all())


def get_user_service(db: Database) -> UserService:
    """Create UserService with database dependency.

    Args:
        db: Injected database session.

    Returns:
        UserService instance.

    Example:
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: int,
            service: UserServiceDep,
        ) -> User:
            user = await service.get_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404)
            return user
    """
    return UserService(db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
```

## Rate Limiter Dependency

```python
"""Rate limiting dependency."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status


@dataclass
class RateLimiter:
    """Simple in-memory rate limiter."""

    requests_per_minute: int = 60
    _requests: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed.

        Args:
            key: Unique identifier (e.g., IP address, user ID).

        Returns:
            True if request is allowed.
        """
        now = time.time()
        minute_ago = now - 60

        # Clean old requests
        self._requests[key] = [t for t in self._requests[key] if t > minute_ago]

        if len(self._requests[key]) >= self.requests_per_minute:
            return False

        self._requests[key].append(now)
        return True


# Singleton rate limiter
_rate_limiter = RateLimiter()


async def check_rate_limit(request: Request) -> None:
    """Check rate limit for the request.

    Args:
        request: The incoming request.

    Raises:
        HTTPException: 429 if rate limit exceeded.

    Example:
        @router.post("/api/expensive-operation")
        async def expensive_operation(
            _: Annotated[None, Depends(check_rate_limit)],
        ) -> dict:
            return {"status": "ok"}
    """
    client_ip = request.client.host if request.client else "unknown"

    if not _rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"},
        )


RateLimited = Annotated[None, Depends(check_rate_limit)]
```

## Test Example: Pagination Dependency

```python
"""Tests for pagination dependency."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dependencies.pagination import Pagination, PaginationParams


@pytest.fixture
def app() -> FastAPI:
    """Create test application."""
    app = FastAPI()

    @app.get("/items")
    async def list_items(pagination: Pagination) -> dict:
        return {
            "offset": pagination.offset,
            "limit": pagination.limit,
            "page": pagination.page,
        }

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestPaginationDependency:
    """Tests for pagination dependency."""

    def test_default_values(self, client: TestClient) -> None:
        """It should use default values when not specified."""
        response = client.get("/items")
        assert response.json() == {"offset": 0, "limit": 20, "page": 1}

    def test_custom_values(self, client: TestClient) -> None:
        """It should accept custom values."""
        response = client.get("/items?offset=40&limit=10")
        assert response.json() == {"offset": 40, "limit": 10, "page": 5}

    def test_limit_validation(self, client: TestClient) -> None:
        """It should reject invalid limit values."""
        response = client.get("/items?limit=0")
        assert response.status_code == 422

        response = client.get("/items?limit=101")
        assert response.status_code == 422

    def test_offset_validation(self, client: TestClient) -> None:
        """It should reject negative offset."""
        response = client.get("/items?offset=-1")
        assert response.status_code == 422
```
