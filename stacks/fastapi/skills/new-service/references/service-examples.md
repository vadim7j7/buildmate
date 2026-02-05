# Async Service Examples

Patterns for async service classes in FastAPI applications.

---

## Example 1: Basic CRUD Service

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Business logic for project operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self, *, skip: int = 0, limit: int = 20) -> list[Project]:
        """List projects with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of project models.
        """
        stmt = select(Project).offset(skip).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, project_id: int) -> Project | None:
        """Get a project by primary key.

        Args:
            project_id: The project ID.

        Returns:
            The project model or None if not found.
        """
        return await self._db.get(Project, project_id)

    async def create(self, payload: ProjectCreate) -> Project:
        """Create a new project.

        Args:
            payload: The project creation data.

        Returns:
            The created project model.
        """
        project = Project(**payload.model_dump())
        self._db.add(project)
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def update(
        self, project_id: int, payload: ProjectUpdate
    ) -> Project | None:
        """Update an existing project.

        Args:
            project_id: The project ID to update.
            payload: The update data (partial).

        Returns:
            The updated project model or None if not found.
        """
        project = await self.get_by_id(project_id)
        if project is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def delete(self, project_id: int) -> bool:
        """Delete a project by ID.

        Args:
            project_id: The project ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        project = await self.get_by_id(project_id)
        if project is None:
            return False
        await self._db.delete(project)
        await self._db.commit()
        return True
```

---

## Example 2: Service with Filtering and Eager Loading

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate


class TaskService:
    """Business logic for task operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_user(
        self,
        *,
        user_id: int,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Task]:
        """List tasks for a user with optional status filter.

        Args:
            user_id: The owner's user ID.
            status_filter: Optional status to filter by.
            skip: Pagination offset.
            limit: Pagination limit.

        Returns:
            List of task models with eagerly loaded project.
        """
        stmt = (
            select(Task)
            .options(selectinload(Task.project))
            .where(Task.assignee_id == user_id)
        )

        if status_filter is not None:
            stmt = stmt.where(Task.status == TaskStatus(status_filter))

        stmt = stmt.offset(skip).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, payload: TaskCreate, *, owner_id: int) -> Task:
        """Create a task assigned to a user.

        Args:
            payload: Task creation data.
            owner_id: The user ID to assign the task to.

        Returns:
            The created task model.
        """
        task = Task(**payload.model_dump(), assignee_id=owner_id)
        self._db.add(task)
        await self._db.commit()
        await self._db.refresh(task)
        return task
```

---

## Example 3: Service with External API Integration

```python
from __future__ import annotations

import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.company import Company

logger = logging.getLogger(__name__)


class CompanyEnrichmentService:
    """Enrich company data from an external API."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def enrich(self, company_id: int) -> bool:
        """Fetch and update company data from external provider.

        Args:
            company_id: The company ID to enrich.

        Returns:
            True if enrichment succeeded, False otherwise.
        """
        company = await self._db.get(Company, company_id)
        if company is None:
            return False

        data = await self._fetch_external_data(company.domain)
        if data is None:
            return False

        company.industry = data.get("industry")
        company.employee_count = data.get("employee_count")
        await self._db.commit()
        return True

    async def _fetch_external_data(self, domain: str) -> dict | None:
        """Fetch company data from external API.

        Args:
            domain: The company domain to look up.

        Returns:
            API response dict or None on failure.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.enrichment_api_url}/companies",
                    params={"domain": domain},
                    headers={"Authorization": f"Bearer {settings.enrichment_api_key}"},
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError:
            logger.exception("Failed to fetch enrichment data for %s", domain)
            return None
```

---

## Key Rules

1. **Inject `AsyncSession`** via constructor, store as `self._db`
2. **All I/O methods are `async`**
3. **Use keyword-only args** for optional parameters (`*,`)
4. **Use `model_dump()`** to convert Pydantic schemas to dicts
5. **Use `model_dump(exclude_unset=True)`** for partial updates
6. **Return `None`/`False`** for not-found cases (let router handle HTTP errors)
7. **Use `selectinload()`** to prevent N+1 queries
8. **Add Google-style docstrings** with Args and Returns sections
9. **Use `logging`** for error reporting (never `print()`)
10. **Handle external API failures** gracefully with try/except
