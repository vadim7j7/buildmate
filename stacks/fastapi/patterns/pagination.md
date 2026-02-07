# FastAPI Pagination Patterns

Pagination patterns for FastAPI with async SQLAlchemy.

---

## 1. Offset-Based Pagination

### Pagination Dependency

```python
"""Pagination dependency for list endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class PaginationParams:
    """Pagination parameters from query string."""

    offset: int
    limit: int

    @property
    def page(self) -> int:
        """Calculate current page (1-indexed)."""
        return (self.offset // self.limit) + 1


def get_pagination(
    offset: Annotated[int, Query(ge=0, description="Records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max records")] = 20,
) -> PaginationParams:
    """Extract pagination parameters from query string."""
    return PaginationParams(offset=offset, limit=limit)


Pagination = Annotated[PaginationParams, Depends(get_pagination)]


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response schema."""

    data: list[T]
    meta: PaginationMeta


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    current_page: int
    per_page: int
    total_pages: int
    total_count: int
    next_page: int | None
    prev_page: int | None
```

### Router Implementation

```python
"""Posts router with pagination."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.pagination import Pagination, PaginatedResponse, PaginationMeta
from app.models.post import Post
from app.schemas.post import PostResponse

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PaginatedResponse[PostResponse])
async def list_posts(
    pagination: Pagination,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaginatedResponse[PostResponse]:
    """List posts with pagination."""
    # Get total count
    count_query = select(func.count()).select_from(Post)
    total_result = await db.execute(count_query)
    total_count = total_result.scalar_one()

    # Get paginated data
    query = (
        select(Post)
        .order_by(Post.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    result = await db.execute(query)
    posts = result.scalars().all()

    # Calculate pagination metadata
    total_pages = (total_count + pagination.limit - 1) // pagination.limit
    current_page = pagination.page

    return PaginatedResponse(
        data=[PostResponse.model_validate(p) for p in posts],
        meta=PaginationMeta(
            current_page=current_page,
            per_page=pagination.limit,
            total_pages=total_pages,
            total_count=total_count,
            next_page=current_page + 1 if current_page < total_pages else None,
            prev_page=current_page - 1 if current_page > 1 else None,
        ),
    )
```

---

## 2. Cursor-Based Pagination

### Cursor Pagination Dependency

```python
"""Cursor-based pagination for large datasets."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class CursorParams:
    """Cursor pagination parameters."""

    cursor: str | None
    limit: int


def get_cursor_pagination(
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Max records")] = 20,
) -> CursorParams:
    """Extract cursor pagination parameters."""
    return CursorParams(cursor=cursor, limit=limit)


CursorPagination = Annotated[CursorParams, Depends(get_cursor_pagination)]


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Cursor-paginated response schema."""

    data: list[T]
    meta: CursorMeta


class CursorMeta(BaseModel):
    """Cursor pagination metadata."""

    next_cursor: str | None
    has_more: bool


def encode_cursor(created_at: datetime, id: str) -> str:
    """Encode pagination cursor."""
    data = {"created_at": created_at.isoformat(), "id": id}
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor: str) -> dict | None:
    """Decode pagination cursor."""
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return data
    except Exception:
        return None
```

### Cursor Pagination Implementation

```python
"""Posts router with cursor pagination."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.cursor_pagination import (
    CursorPagination,
    CursorPaginatedResponse,
    CursorMeta,
    decode_cursor,
    encode_cursor,
)
from app.models.post import Post
from app.schemas.post import PostResponse

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=CursorPaginatedResponse[PostResponse])
async def get_feed(
    pagination: CursorPagination,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CursorPaginatedResponse[PostResponse]:
    """Get feed with cursor pagination."""
    query = select(Post).order_by(Post.created_at.desc(), Post.id.desc())

    # Apply cursor filter
    if pagination.cursor:
        cursor_data = decode_cursor(pagination.cursor)
        if cursor_data:
            query = query.where(
                or_(
                    Post.created_at < cursor_data["created_at"],
                    and_(
                        Post.created_at == cursor_data["created_at"],
                        Post.id < cursor_data["id"],
                    ),
                )
            )

    # Fetch one extra to check for more
    query = query.limit(pagination.limit + 1)
    result = await db.execute(query)
    posts = list(result.scalars().all())

    # Determine if there are more results
    has_more = len(posts) > pagination.limit
    if has_more:
        posts = posts[: pagination.limit]

    # Generate next cursor
    next_cursor = None
    if has_more and posts:
        last_post = posts[-1]
        next_cursor = encode_cursor(last_post.created_at, last_post.id)

    return CursorPaginatedResponse(
        data=[PostResponse.model_validate(p) for p in posts],
        meta=CursorMeta(next_cursor=next_cursor, has_more=has_more),
    )
```

---

## 3. Paginated Service Pattern

```python
"""Paginated service for reusable pagination logic."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.pagination import PaginatedResponse, PaginationMeta, PaginationParams

T = TypeVar("T")
M = TypeVar("M")  # Model type


class PaginatedService(Generic[M, T]):
    """Base service with pagination support."""

    def __init__(self, db: AsyncSession, model: type[M], schema: type[T]) -> None:
        """Initialize with database session and model."""
        self.db = db
        self.model = model
        self.schema = schema

    async def list_paginated(
        self,
        pagination: PaginationParams,
        base_query: Select | None = None,
    ) -> PaginatedResponse[T]:
        """List records with pagination."""
        if base_query is None:
            base_query = select(self.model)

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar_one()

        # Get paginated data
        query = base_query.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        # Calculate metadata
        total_pages = (total_count + pagination.limit - 1) // pagination.limit
        current_page = pagination.page

        return PaginatedResponse(
            data=[self.schema.model_validate(item) for item in items],
            meta=PaginationMeta(
                current_page=current_page,
                per_page=pagination.limit,
                total_pages=total_pages,
                total_count=total_count,
                next_page=current_page + 1 if current_page < total_pages else None,
                prev_page=current_page - 1 if current_page > 1 else None,
            ),
        )


# Usage in router
@router.get("", response_model=PaginatedResponse[PostResponse])
async def list_posts(
    pagination: Pagination,
    status: str | None = None,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaginatedResponse[PostResponse]:
    """List posts with filtering and pagination."""
    service = PaginatedService(db, Post, PostResponse)

    query = select(Post).order_by(Post.created_at.desc())
    if status:
        query = query.where(Post.status == status)

    return await service.list_paginated(pagination, query)
```

---

## 4. Filtered Pagination

```python
"""Posts router with filtering and pagination."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.pagination import Pagination, PaginatedResponse
from app.models.post import Post
from app.schemas.post import PostResponse

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PaginatedResponse[PostResponse])
async def list_posts(
    pagination: Pagination,
    db: Annotated[AsyncSession, Depends(get_db)],
    # Filter parameters
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    author_id: Annotated[str | None, Query(description="Filter by author")] = None,
    from_date: Annotated[date | None, Query(description="From date")] = None,
    to_date: Annotated[date | None, Query(description="To date")] = None,
    search: Annotated[str | None, Query(description="Search term")] = None,
    # Sort parameters
    sort_by: Annotated[str, Query(description="Sort field")] = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> PaginatedResponse[PostResponse]:
    """List posts with filtering, sorting, and pagination."""
    query = select(Post)

    # Apply filters
    if status:
        query = query.where(Post.status == status)
    if author_id:
        query = query.where(Post.author_id == author_id)
    if from_date:
        query = query.where(Post.created_at >= from_date)
    if to_date:
        query = query.where(Post.created_at <= to_date)
    if search:
        query = query.where(
            Post.title.ilike(f"%{search}%") | Post.body.ilike(f"%{search}%")
        )

    # Apply sorting
    sort_column = getattr(Post, sort_by, Post.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Execute with pagination
    service = PaginatedService(db, Post, PostResponse)
    return await service.list_paginated(pagination, query)
```

---

## 5. FastAPI-Pagination Library

```python
"""Using fastapi-pagination library."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.post import Post
from app.schemas.post import PostResponse

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=Page[PostResponse])
async def list_posts(
    db: AsyncSession = Depends(get_db),
) -> Page[PostResponse]:
    """List posts with pagination."""
    query = select(Post).order_by(Post.created_at.desc())
    return await paginate(db, query)


# Add pagination to app
add_pagination(app)
```

---

## 6. Link Headers (RFC 5988)

```python
"""Pagination with Link headers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/posts", tags=["posts"])


def build_link_header(
    request: Request,
    current_page: int,
    total_pages: int,
    per_page: int,
) -> str:
    """Build RFC 5988 Link header."""
    base_url = str(request.url).split("?")[0]
    links = []

    if current_page > 1:
        links.append(f'<{base_url}?page={current_page - 1}&per_page={per_page}>; rel="prev"')
    if current_page < total_pages:
        links.append(f'<{base_url}?page={current_page + 1}&per_page={per_page}>; rel="next"')
    links.append(f'<{base_url}?page=1&per_page={per_page}>; rel="first"')
    links.append(f'<{base_url}?page={total_pages}&per_page={per_page}>; rel="last"')

    return ", ".join(links)


@router.get("")
async def list_posts(
    request: Request,
    response: Response,
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[PostResponse]:
    """List posts with Link header pagination."""
    offset = (page - 1) * per_page

    # Get total count
    count_result = await db.execute(select(func.count()).select_from(Post))
    total_count = count_result.scalar_one()
    total_pages = (total_count + per_page - 1) // per_page

    # Get data
    query = select(Post).order_by(Post.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    posts = result.scalars().all()

    # Set headers
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Total-Pages"] = str(total_pages)
    response.headers["Link"] = build_link_header(request, page, total_pages, per_page)

    return [PostResponse.model_validate(p) for p in posts]
```

---

## 7. Testing Pagination

```python
"""Tests for pagination."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_pagination_first_page(client: AsyncClient, posts: list):
    """Test first page of results."""
    response = await client.get("/api/posts?offset=0&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 10
    assert data["meta"]["current_page"] == 1
    assert data["meta"]["per_page"] == 10


@pytest.mark.asyncio
async def test_pagination_second_page(client: AsyncClient, posts: list):
    """Test second page of results."""
    response = await client.get("/api/posts?offset=10&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["current_page"] == 2
    assert data["meta"]["prev_page"] == 1


@pytest.mark.asyncio
async def test_pagination_cursor(client: AsyncClient, posts: list):
    """Test cursor-based pagination."""
    # Get first page
    response = await client.get("/api/feed?limit=10")
    data = response.json()
    assert len(data["data"]) == 10
    assert data["meta"]["has_more"] is True
    cursor = data["meta"]["next_cursor"]

    # Get second page with cursor
    response = await client.get(f"/api/feed?cursor={cursor}&limit=10")
    data = response.json()
    assert len(data["data"]) == 10


@pytest.mark.asyncio
async def test_pagination_limit_validation(client: AsyncClient):
    """Test pagination limit validation."""
    response = await client.get("/api/posts?limit=0")
    assert response.status_code == 422

    response = await client.get("/api/posts?limit=101")
    assert response.status_code == 422
```
