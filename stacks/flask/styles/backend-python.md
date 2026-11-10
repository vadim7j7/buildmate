# Python Style Guide

Code style rules for Flask projects (synchronous: Flask 3 + Flask-SQLAlchemy 3.1). All rules are enforced by Ruff and mypy.
Agents must follow these conventions when generating or modifying code.

---

## 1. Annotations Stay Runtime-Evaluated (no `from __future__ import annotations`)

Target Python 3.13: `str | None` and `list[int]` work natively, so the future import
is not needed. **Do not add `from __future__ import annotations`.** It turns every
annotation into a string that Pydantic and SQLAlchemy must resolve at runtime, and ruff's
`TC` (flake8-type-checking) rules then tell you to move the "annotation-only" imports
into `if TYPE_CHECKING:` blocks. Those imports are needed at runtime, so the app fails
at startup (`NameError`, `PydanticUndefinedAnnotation`, unresolved `Mapped[...]`).

Never move an import into `if TYPE_CHECKING:` when the name is used by a Pydantic model field, a SQLAlchemy `Mapped[]` column or a function whose signature is inspected at runtime.
Quote forward references to classes defined later or in another module:

```python
# CORRECT
from datetime import datetime

from pydantic import BaseModel


class Event(BaseModel):
    at: datetime  # datetime must be a real import
    parent: "Event | None" = None  # forward reference: quote it

# WRONG - stringifies annotations; ruff TC then moves runtime imports away
from __future__ import annotations
```

---

## 2. Type Annotations

All function parameters and return types must be annotated. Use modern syntax:

```python
# CORRECT
def get_user(user_id: int) -> User | None: ...
def list_users(skip: int = 0) -> list[User]: ...
def process(data: dict[str, Any]) -> None: ...

# WRONG - legacy typing imports
from typing import Optional, List, Dict
def get_user(user_id: int) -> Optional[User]: ...
def list_users(skip: int = 0) -> List[User]: ...
```

---

## 3. Docstrings (Google Style)

All public classes, functions, and methods must have Google-style docstrings:

```python
class ProjectService:
    """Business logic for project operations."""

    def create(self, payload: ProjectCreate, *, owner_id: int) -> Project:
        """Create a new project.

        Args:
            payload: The project creation data.
            owner_id: ID of the owning user.

        Returns:
            The created project model.

        Raises:
            IntegrityError: If a project with the same name exists.
        """
```

Rules:
- First line is a one-sentence summary
- `Args:` section for parameters (skip `self`)
- `Returns:` section for return values
- `Raises:` section for exceptions (optional)
- Use 4-space indentation inside docstring sections

---

## 4. Naming Conventions

| Element      | Convention           | Example                    |
|-------------|----------------------|----------------------------|
| Function     | `snake_case`         | `get_user`, `create_project` |
| Method       | `snake_case`         | `def list(self)`           |
| Variable     | `snake_case`         | `user_id`, `project_name`  |
| Class        | `PascalCase`         | `ProjectService`, `UserRead` |
| Constant     | `SCREAMING_SNAKE`    | `MAX_RETRIES`, `API_VERSION` |
| Module       | `snake_case`         | `project_service.py`       |
| Package      | `snake_case`         | `models/`, `services/`     |
| Test class   | `Test` + `PascalCase`| `TestProjectService`       |
| Test method  | `test_` + `snake_case` | `test_create_project`    |
| Private      | `_` prefix           | `self._db`, `_helper()`    |

---

## 5. Import Organization

Imports are ordered in three groups, separated by blank lines:

1. **Standard library** (`os`, `datetime`, `collections.abc`)
2. **Third-party** (`flask`, `sqlalchemy`, `pydantic`)
3. **Local** (`app.models`, `app.schemas`, `app.services`)

Ruff's isort rules enforce this automatically.

```python
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from app.extensions import db
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.project_service import ProjectService
```

---

## 6. String Formatting

Use f-strings for all string formatting:

```python
# CORRECT
message = f"Project {project_id} not found"
logger.info("Processing %d items", count)  # logging uses % style

# WRONG
message = "Project {} not found".format(project_id)
message = "Project %d not found" % project_id
```

Exception: Use `%`-style formatting in `logging` calls for lazy evaluation.

---

## 7. Error Handling

Catch specific exceptions. Never use bare `except`:

```python
# CORRECT
try:
    result = external_api.fetch(resource_id)
except httpx.HTTPStatusError as exc:
    logger.error("API call failed: %s", exc)
    return None
except httpx.ConnectError:
    logger.error("Connection failed")
    raise

# WRONG
try:
    result = external_api.fetch(resource_id)
except Exception:
    pass
```

---

## 8. Synchronous I/O (no async)

Flask views, services and Flask-SQLAlchemy's `db.session` are synchronous. Write
plain `def` functions; never `async def` views/services, `await`, or
`async with db.session()` (Flask-SQLAlchemy's session is not an async context manager —
`TypeError`). Use sync clients (`httpx.Client`, `requests`) with timeouts.

```python
# CORRECT
def get_user(user_id: int) -> User | None:
    return db.session.get(User, user_id)

# WRONG - Flask-SQLAlchemy is sync
async def get_user(user_id: int) -> User | None:
    async with db.session() as session:  # TypeError
        return await session.get(User, user_id)
```

---

## 9. Pydantic Conventions

Use Pydantic v2 API exclusively:

```python
# CORRECT (Pydantic v2)
schema.model_dump()
schema.model_dump(exclude_unset=True)
schema.model_validate(data)
model_config = ConfigDict(from_attributes=True)

# WRONG (deprecated Pydantic v1 API)
schema.dict()
schema.parse_obj(data)

class Config:
    orm_mode = True
```

---

## 10. SQLAlchemy Conventions

Use SQLAlchemy 2.0 API exclusively:

```python
# CORRECT (SQLAlchemy 2.0)
class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

stmt = select(User).where(User.id == user_id)
user = db.session.execute(stmt).scalar_one_or_none()

# WRONG (legacy SQLAlchemy)
class User(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(255))

user = User.query.filter(User.id == user_id).first()  # legacy Query API
```

---

## 11. Line Length and Formatting

- Maximum line length: **88 characters** (Ruff default)
- Use trailing commas in multi-line collections
- Use parentheses for line continuation (not backslash)

```python
# CORRECT
result = service.list_for_user(
    user_id=current_user.id,
    status_filter=status_filter,
    skip=skip,
    limit=limit,
)

# WRONG
result = service.list_for_user(user_id=current_user.id, \
    status_filter=status_filter, skip=skip, limit=limit)
```

---

## 12. Logging

Use the standard `logging` module with module-level loggers:

```python
import logging

logger = logging.getLogger(__name__)


class MyService:
    def process(self, item_id: int) -> None:
        logger.info("Processing item %d", item_id)
        try:
            # ...
            logger.info("Item %d processed successfully", item_id)
        except ValueError:
            logger.exception("Failed to process item %d", item_id)
```

Rules:
- Use `logging.getLogger(__name__)` at module level
- Use `%`-style formatting in log calls (lazy evaluation)
- Use `logger.exception()` in except blocks (includes traceback)
- Never log sensitive data (passwords, tokens, PII)

---

## 13. Constants and Configuration

Use module-level constants and the class-based Flask config from
`patterns/flask-patterns.md` (`CONFIGS` mapping, values from environment variables):

```python
# Constants in module
MAX_RETRIES = 3
DEFAULT_PAGE_SIZE = 20

# Configuration: app.config via config classes, read with current_app.config
from flask import current_app

page_size = current_app.config.get("PAGE_SIZE", DEFAULT_PAGE_SIZE)
```

---

## 14. Ruff Configuration Reference

Standard `pyproject.toml` configuration:

```toml
[tool.ruff]
target-version = "py313"
line-length = 88

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "TC",   # flake8-type-checking (safe: no future import, see section 1)
    "RUF",  # ruff-specific rules
]

[tool.ruff.lint.isort]
known-first-party = ["app"]

[tool.ruff.lint.flake8-type-checking]
# Safety net: never move imports that these classes resolve at runtime
runtime-evaluated-base-classes = [
    "pydantic.BaseModel",
    "sqlalchemy.orm.DeclarativeBase",
    "app.extensions.Base",  # the project's own DeclarativeBase subclass
]

[tool.mypy]
python_version = "3.13"
strict = true
plugins = ["pydantic.mypy"]  # SQLAlchemy 2.0 `Mapped[]` needs no plugin

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-v --tb=short"
```
