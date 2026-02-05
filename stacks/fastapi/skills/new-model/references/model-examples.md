# SQLAlchemy 2.0 Model Examples

Examples using the modern `Mapped[]` annotation style.

---

## Example 1: Basic Model with Timestamps

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Project(Base):
    """SQLAlchemy model for the projects table."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
```

---

## Example 2: Model with Foreign Key and Relationship

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Task(Base):
    """SQLAlchemy model for the tasks table."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped[Project] = relationship(back_populates="tasks")
```

---

## Example 3: Model with Enum and Index

```python
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskStatus(str, enum.Enum):
    """Enum for task status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(Base):
    """SQLAlchemy model for tasks with enum status and indices."""

    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_project_status", "project_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING
    )
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="tasks")
    assignee: Mapped[User | None] = relationship()
```

---

## Example 4: Model with Many-to-Many Relationship

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, ForeignKey, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Association table for many-to-many
project_tags = Table(
    "project_tags",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    """SQLAlchemy model for tags."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    projects: Mapped[list[Project]] = relationship(
        secondary=project_tags, back_populates="tags"
    )


class Project(Base):
    """SQLAlchemy model for projects with tags."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    tags: Mapped[list[Tag]] = relationship(
        secondary=project_tags, back_populates="projects"
    )
```

---

## Key Rules

1. **Always use `Mapped[]`** type annotations (never legacy `Column()`)
2. **Always use `mapped_column()`** for column definitions
3. **Always set `__tablename__`** explicitly
4. **Always include** `id`, `created_at`, `updated_at` columns
5. **Use `server_default=func.now()`** for timestamp defaults
6. **Use `String(N)`** for varchar columns with explicit length
7. **Use `Text`** for unlimited text columns
8. **Use `ForeignKey()`** inside `mapped_column()` for relationships
9. **Use `relationship()`** with `back_populates` for bidirectional relationships
10. **Use `Mapped[X | None]`** for nullable columns
11. **Add composite indices** via `__table_args__` for common query patterns
