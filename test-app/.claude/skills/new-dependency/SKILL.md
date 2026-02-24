---
name: new-dependency
description: Generate a FastAPI dependency injection function
---

# /new-dependency

## What This Does

Generates a FastAPI dependency function for injecting services, database
sessions, authentication, or other shared resources. Supports both simple
functions and class-based dependencies with `__call__`.

## Usage

```
/new-dependency database             # Creates get_db session dependency
/new-dependency current_user         # Creates auth dependency
/new-dependency settings             # Creates settings dependency
/new-dependency pagination           # Creates pagination params dependency
/new-dependency rate_limiter         # Creates rate limiting dependency
```

## How It Works

1. **Read reference patterns.** Load dependency patterns from:
   - `skills/new-dependency/references/dependency-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-python.md`

2. **Determine dependency type.** Parse the argument to determine:
   - Dependency name and purpose
   - Whether it needs database access
   - Whether it's cacheable or per-request

3. **Generate the dependency file.** Create the dependency with:
   - `from __future__ import annotations`
   - `Depends` import from FastAPI
   - `Annotated` types for cleaner signatures
   - Generator pattern for cleanup (if needed)
   - Type annotations

4. **Generate the test file.** Create the test with:
   - Override fixtures
   - Tests for dependency behavior
   - Error handling tests

5. **Run quality checks.**

   ```bash
   uv run ruff format src/app/dependencies/<name>.py tests/dependencies/test_<name>.py
   uv run ruff check src/app/dependencies/<name>.py tests/dependencies/test_<name>.py
   uv run mypy src/app/dependencies/<name>.py
   ```

6. **Report results.** Show the generated files.

## Generated Files

```
src/app/dependencies/<name>.py
tests/dependencies/test_<name>.py
```

## Example Output

For `/new-dependency pagination`:

**Dependency:** `src/app/dependencies/pagination.py`
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

    @property
    def has_next(self) -> bool:
        """Check if there could be more results."""
        return True  # Caller should check against total


def get_pagination(
    offset: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Max records to return")
    ] = 20,
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
            pagination: Annotated[PaginationParams, Depends(get_pagination)],
        ) -> list[Item]:
            return await service.list(
                offset=pagination.offset,
                limit=pagination.limit,
            )
    """
    return PaginationParams(offset=offset, limit=limit)


# Type alias for cleaner route signatures
Pagination = Annotated[PaginationParams, Depends(get_pagination)]
```

For `/new-dependency current_user`:

**Dependency:** `src/app/dependencies/auth.py`
```python
"""Authentication dependencies for protected routes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth_service import AuthService, get_auth_service

if TYPE_CHECKING:
    from app.models.user import User

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
    """Optionally extract user, returning None for unauthenticated requests."""
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

**Test:** `tests/dependencies/test_auth.py`

## Rules

- Use `Annotated` for cleaner dependency injection signatures
- Create type aliases for commonly used dependencies
- Use `async def` for dependencies that perform I/O
- Use generator pattern (`yield`) for cleanup (db sessions, connections)
- Document dependencies with docstrings showing usage examples
- Dependencies should be idempotent and side-effect free
- Use `@lru_cache` for expensive singleton dependencies
- Handle errors appropriately (raise `HTTPException` with proper status)
