# Pydantic v2 Schema Examples

Examples of Pydantic v2 schema patterns for FastAPI applications.

---

## Example 1: Basic CRUD Schema Set

```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    """Shared fields for project schemas."""

    name: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""


class ProjectUpdate(BaseModel):
    """Schema for updating a project (all fields optional)."""

    name: str | None = None
    description: str | None = None


class ProjectRead(ProjectBase):
    """Schema for reading a project (includes DB fields)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
```

---

## Example 2: Schema with Validators

```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class UserBase(BaseModel):
    """Shared fields for user schemas."""

    email: str
    username: str
    full_name: str | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3:
            msg = "Username must be at least 3 characters"
            raise ValueError(msg)
        return v


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            msg = "Password must be at least 8 characters"
            raise ValueError(msg)
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    full_name: str | None = None
    email: str | None = None


class UserRead(UserBase):
    """Schema for reading a user (no password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
```

---

## Example 3: Nested Schema with Relationships

```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    """Shared fields for task schemas."""

    title: str
    description: str | None = None
    status: str = "pending"


class TaskCreate(TaskBase):
    """Schema for creating a task."""

    project_id: int


class TaskRead(TaskBase):
    """Schema for reading a task with project info."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    created_at: datetime


class ProjectWithTasks(BaseModel):
    """Schema for a project with its tasks."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    tasks: list[TaskRead] = []
```

---

## Example 4: Pagination Response

```python
from __future__ import annotations

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    items: list
    total: int
    skip: int
    limit: int
    has_more: bool


class PaginatedProjects(BaseModel):
    """Paginated project response."""

    items: list[ProjectRead]
    total: int
    skip: int
    limit: int
    has_more: bool
```

---

## Key Rules

1. **Always use `from __future__ import annotations`**
2. **`ConfigDict(from_attributes=True)`** on Read schemas for ORM compatibility
3. **`str | None`** syntax, not `Optional[str]`
4. **`list[X]`** syntax, not `List[X]`
5. **Docstrings** on all schema classes
6. **Validators** use `@field_validator` with `@classmethod`
7. **`model_dump()`** to serialize, never `.dict()`
8. **`model_validate()`** to parse, never `.parse_obj()`
9. **Update schemas** have all fields optional for partial updates
10. **Create schemas** may add fields not in Base (e.g., `password`)
