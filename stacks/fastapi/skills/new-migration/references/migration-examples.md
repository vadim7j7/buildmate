# Alembic Migration Examples

Patterns for writing safe, reversible Alembic migrations.

---

## Example 1: Create Table

```python
"""create projects table

Revision ID: abc123
Revises: None
Create Date: 2026-01-15 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "abc123"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("projects")
```

---

## Example 2: Add Column

```python
"""add role column to users

Revision ID: def456
Revises: abc123
Create Date: 2026-01-16 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "def456"
down_revision = "abc123"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),
    )
    op.create_index("ix_users_role", "users", ["role"])


def downgrade() -> None:
    op.drop_index("ix_users_role", table_name="users")
    op.drop_column("users", "role")
```

---

## Example 3: Add Foreign Key

```python
"""add project_id to tasks

Revision ID: ghi789
Revises: def456
Create Date: 2026-01-17 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "ghi789"
down_revision = "def456"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("project_id", sa.Integer(), nullable=False),
    )
    op.create_foreign_key(
        "fk_tasks_project_id",
        "tasks",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_tasks_project_id", table_name="tasks")
    op.drop_constraint("fk_tasks_project_id", "tasks", type_="foreignkey")
    op.drop_column("tasks", "project_id")
```

---

## Example 4: Create Enum Column

```python
"""add status enum to tasks

Revision ID: jkl012
Revises: ghi789
Create Date: 2026-01-18 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "jkl012"
down_revision = "ghi789"
branch_labels = None
depends_on = None

task_status = sa.Enum("pending", "in_progress", "completed", "cancelled", name="taskstatus")


def upgrade() -> None:
    task_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "tasks",
        sa.Column("status", task_status, nullable=False, server_default="pending"),
    )
    op.create_index("ix_tasks_status", "tasks", ["status"])


def downgrade() -> None:
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_column("tasks", "status")
    task_status.drop(op.get_bind(), checkfirst=True)
```

---

## Example 5: Data Migration

```python
"""backfill user full_name from first and last name

Revision ID: mno345
Revises: jkl012
Create Date: 2026-01-19 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "mno345"
down_revision = "jkl012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the new column
    op.add_column(
        "users",
        sa.Column("full_name", sa.String(255), nullable=True),
    )

    # Backfill data
    op.execute(
        "UPDATE users SET full_name = first_name || ' ' || last_name "
        "WHERE full_name IS NULL"
    )

    # Make non-nullable after backfill
    op.alter_column("users", "full_name", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "full_name")
```

---

## Async Alembic env.py Setup

```python
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    url = settings.database_url
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in online mode with async engine."""
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

---

## Key Rules

1. **Always include `downgrade()`** that fully reverses `upgrade()`
2. **Name constraints explicitly** (`fk_`, `ix_`, `uq_` prefixes)
3. **Use `server_default`** instead of Python-side defaults for new columns
4. **Make new columns nullable** or provide a `server_default`
5. **Create indices** for foreign keys and frequently filtered columns
6. **Use `from __future__ import annotations`** in all migration files
7. **Test rollback** after every migration: `alembic downgrade -1`
