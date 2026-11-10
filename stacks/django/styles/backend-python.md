# Python Style Guide

Code style rules for Django + Django REST Framework projects. All rules are enforced by
Ruff and mypy (with django-stubs). Django code is **synchronous by default**.
Agents must follow these conventions when generating or modifying code.

---

## 1. No `from __future__ import annotations`

Target Python 3.13: `str | None` and `list[int]` work natively. Do not add
`from __future__ import annotations` (same rule as every Python stack here: it lets
ruff's `TC` rules move imports into `if TYPE_CHECKING:` that code needs at runtime).
Quote forward references instead (`-> "ProjectQuerySet"`).

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
class ProjectCreateService:
    """Business logic for creating projects."""

    def execute(self, *, owner: User, data: dict[str, Any]) -> Project:
        """Create a new project.

        Args:
            owner: The user who owns the project.
            data: Validated serializer data.

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
| Method       | `snake_case`         | `def execute(self)`        |
| Variable     | `snake_case`         | `user_id`, `project_name`  |
| Class        | `PascalCase`         | `ProjectService`, `UserRead` |
| Constant     | `SCREAMING_SNAKE`    | `MAX_RETRIES`, `API_VERSION` |
| Module       | `snake_case`         | `project_service.py`       |
| App/package  | `snake_case`         | `projects/`, `services/`   |
| Test class   | `Test` + `PascalCase`| `TestProjectViewSet`       |
| Test method  | `test_` + `snake_case` | `test_create_project`    |
| Private      | `_` prefix           | `self._db`, `_helper()`    |

---

## 5. Import Organization

Imports are ordered in three groups, separated by blank lines:

1. **Standard library** (`os`, `datetime`, `collections.abc`)
2. **Third-party** (`django`, `rest_framework`)
3. **Local** (`config`, `projects.models`, `projects.services`, relative `.models`)

Ruff's isort rules enforce this automatically.

```python
import logging
from datetime import datetime

from django.db import transaction
from rest_framework import viewsets

from projects.models import Project
from projects.services.project_archive import ProjectArchiveService
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
except requests.HTTPError as exc:
    logger.error("API call failed: %s", exc)
    return None
except requests.ConnectionError:
    logger.error("Connection failed")
    raise

# WRONG
try:
    result = external_api.fetch(resource_id)
except Exception:
    pass
```

---

## 8. Sync by Default

Views, services, signals, management commands and ORM access are synchronous `def`.
Do not write `async def` views or services unless the whole request path is async
(then use the ORM's `a`-prefixed methods such as `aget()`, `acreate()`, and
`sync_to_async` for sync-only code). Never call the sync ORM from an `async def`
(`SynchronousOnlyOperation`). Use timeouts on outbound HTTP (`requests`/`httpx.Client`).

```python
# CORRECT
def archive(project_id: int) -> Project:
    project = Project.objects.select_related("owner").get(pk=project_id)
    ...

# WRONG - sync ORM inside async code
async def archive(project_id: int) -> Project:
    return Project.objects.get(pk=project_id)  # SynchronousOnlyOperation
```

---

## 9. Serializer Conventions (DRF)

```python
# CORRECT
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "owner", "created_at"]  # explicit list
        read_only_fields = ["id", "owner", "created_at"]

    def validate_name(self, value: str) -> str:
        if value.strip() == "":
            raise serializers.ValidationError("Name is required.")
        return value

# WRONG
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"  # leaks new columns automatically
```

- Validation lives in serializers (`validate_<field>`, `validate`), not in views
- Call `serializer.is_valid(raise_exception=True)`; read `serializer.validated_data`

---

## 10. Django ORM Conventions

```python
# CORRECT
from django.conf import settings

owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
projects = Project.objects.filter(owner=user).select_related("owner").prefetch_related("tasks")
exists = Project.objects.filter(name=name).exists()
Project.objects.filter(pk=pk).update(views=F("views") + 1)

# WRONG
owner = models.ForeignKey("auth.User", on_delete=models.CASCADE)  # breaks custom user models
for p in Project.objects.all():
    p.owner.username  # N+1 query
if Project.objects.filter(name=name).count() > 0: ...
```

- `settings.AUTH_USER_MODEL` in FKs, `get_user_model()` in code
- `select_related` / `prefetch_related` for every relation you read
- `transaction.atomic()` around multi-write operations; `save(update_fields=[...])`
- Raw SQL only via parameterized `cursor.execute(sql, params)` (never f-strings)

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

Configuration lives in `config/settings.py` and comes from environment variables
(see `patterns/django-patterns.md`): required secrets use `os.environ["NAME"]` (fail
at startup), `DEBUG = os.environ.get("DJANGO_DEBUG") == "1"`. Read settings with
`from django.conf import settings`; never import `config.settings` directly.

```python
# Constants in module
MAX_RETRIES = 3

# Settings access
from django.conf import settings

page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]
```

---

## 14. Ruff, mypy and pytest Configuration Reference

Standard `pyproject.toml` configuration. Apps live at the project root, so ruff and
mypy run on `.` (the quality gates are `ruff check .`, `ruff format --check .`,
`mypy .`, `pytest`).

```toml
[tool.ruff]
target-version = "py313"
line-length = 88
extend-exclude = ["**/migrations"]

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
    "DJ",   # flake8-django
    "TC",   # flake8-type-checking
    "RUF",  # ruff-specific rules
]
ignore = [
    "RUF012",  # Django/DRF class attributes (Meta.fields, permission_classes) are lists
]

[tool.ruff.lint.isort]
known-first-party = ["config"]  # add each local app: "projects", "users", ...

[tool.mypy]
python_version = "3.13"
strict = true
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
exclude = ["/migrations/"]

[[tool.mypy.overrides]]
module = ["*.migrations.*", "*.tests.*", "conftest"]
disallow_untyped_defs = false

[tool.django-stubs]
django_settings_module = "config.settings"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["test_*.py"]
addopts = "-v --tb=short --reuse-db"
```

Dev dependencies: `ruff`, `mypy`, `django-stubs[compatible-mypy]`,
`djangorestframework-stubs[compatible-mypy]`, `pytest`, `pytest-django`, `factory-boy`.
The django-stubs plugin and pytest-django import the settings module, so
`DJANGO_SECRET_KEY` must be set when running mypy and pytest (CI env, local `.env`).
