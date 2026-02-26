# Python Style Guide

Code style rules for Python projects. All rules are enforced by Ruff and mypy.
Agents must follow these conventions when generating or modifying code.

---

## 1. Future Annotations

Every Python module must start with `from __future__ import annotations` as the
first import. This enables PEP 604 union syntax (`str | None`) and forward references.

```python
# CORRECT
from __future__ import annotations

from pydantic import BaseModel

# WRONG - missing future annotations
from pydantic import BaseModel
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

    async def create(self, payload: ProjectCreate) -> Project:
        """Create a new project.

        Args:
            payload: The project creation data.

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
| Method       | `snake_case`         | `async def list(self)`     |
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
2. **Third-party** (`sqlalchemy`, `pydantic`)
3. **Local** (`app.models`, `app.schemas`, `app.services`)

Ruff's isort rules enforce this automatically.

```python
from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
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
    result = await external_api.fetch(resource_id)
except httpx.HTTPStatusError as exc:
    logger.error("API call failed: %s", exc)
    return None
except httpx.ConnectError:
    logger.error("Connection failed")
    raise

# WRONG
try:
    result = await external_api.fetch(resource_id)
except Exception:
    pass
```

---

## 8. Async/Await

All I/O operations must be async. Never use synchronous I/O in async contexts:

```python
# CORRECT
async def get_user(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)

# WRONG - blocking I/O in async context
async def get_data(url: str) -> dict:
    import requests
    return requests.get(url).json()  # Blocks the event loop!
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
class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

stmt = select(User).where(User.id == user_id)
result = await db.execute(stmt)

# WRONG (legacy SQLAlchemy)
class User(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(255))

result = db.query(User).filter(User.id == user_id).first()
```

---

## 11. Line Length and Formatting

- Maximum line length: **88 characters** (Ruff default)
- Use trailing commas in multi-line collections
- Use parentheses for line continuation (not backslash)

```python
# CORRECT
result = await service.list_for_user(
    user_id=current_user.id,
    status_filter=status_filter,
    skip=skip,
    limit=limit,
)

# WRONG
result = await service.list_for_user(user_id=current_user.id, \
    status_filter=status_filter, skip=skip, limit=limit)
```

---

## 12. Logging

Use the standard `logging` module with module-level loggers:

```python
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MyService:
    async def process(self, item_id: int) -> None:
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

Use module-level constants and Pydantic Settings:

```python
# Constants in module
MAX_RETRIES = 3
DEFAULT_PAGE_SIZE = 20

# Configuration via Pydantic Settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False
```

---

## 14. Ruff Configuration Reference

Standard `pyproject.toml` configuration:

```toml
[tool.ruff]
target-version = "py312"
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
    "TCH",  # flake8-type-checking
    "RUF",  # ruff-specific rules
]

[tool.ruff.lint.isort]
known-first-party = ["app"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy", "sqlalchemy.ext.mypy.plugin"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"
```
