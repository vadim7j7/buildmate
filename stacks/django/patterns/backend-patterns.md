# Python Backend Code Patterns (Django)

Service layer, querysets, transactions and configuration for Django + DRF. Read with
`patterns/django-patterns.md` (layout, models, serializers, ViewSets, URLs, settings,
tests). Django code here is **synchronous**: the ORM, services and views are plain
`def` (no SQLAlchemy, no Pydantic, no `AsyncSession`).

---

## 1. Where Logic Lives

| Layer | Holds | Must not |
|-------|-------|----------|
| `models.py` | Fields, constraints, `__str__`, small per-row helpers, custom QuerySet/Manager | Call external services |
| `serializers.py` | Input validation, output shape | Run multi-model business flows |
| `services/` | Business logic, multi-model writes, transactions, external calls | Know about `Request`/`Response` |
| `views.py` | Auth/permissions, pick queryset + serializer, call a service | Contain business rules or raw queries beyond `get_queryset()` |

---

## 2. Service Pattern

One service class per use case, in `<app>/services/<use_case>.py`, with a single public
`execute()` method. Inject collaborators through the constructor so tests can pass fakes.

```python
# projects/services/project_archive.py
import logging

from django.db import transaction

from projects.exceptions import ProjectAlreadyArchivedError
from projects.models import Project
from projects.notifications import Notifier, default_notifier

logger = logging.getLogger(__name__)


class ProjectArchiveService:
    """Archive a project and notify its members."""

    def __init__(self, notifier: Notifier | None = None) -> None:
        self._notifier = notifier or default_notifier()

    def execute(self, project: Project) -> Project:
        """Archive ``project``.

        Args:
            project: The project to archive.

        Returns:
            The archived project.

        Raises:
            ProjectAlreadyArchivedError: If the project is already archived.
        """
        with transaction.atomic():
            # Lock the row so two concurrent archives cannot both pass the check
            locked = Project.objects.select_for_update().get(pk=project.pk)
            if not locked.is_active:
                raise ProjectAlreadyArchivedError(project.pk)
            locked.is_active = False
            locked.save(update_fields=["is_active", "updated_at"])
            # Side effects run only after the commit succeeds
            transaction.on_commit(lambda: self._notifier.project_archived(locked.pk))

        logger.info("Archived project %s", locked.pk)
        return locked
```

```python
# projects/exceptions.py
class ProjectError(Exception):
    """Base exception for the projects app."""


class ProjectAlreadyArchivedError(ProjectError):
    """Raised when archiving a project that is already archived."""
```

### Service Rules

- Sync `def` methods; use the Django ORM, never SQLAlchemy sessions
- Wrap multi-write operations in `transaction.atomic()` (block or decorator)
- Use `select_for_update()` inside the transaction when a check-then-write can race
- Put emails, webhooks and task enqueues in `transaction.on_commit(...)`
- Raise domain exceptions (`<app>/exceptions.py`); views map them to HTTP errors
  (e.g. raise `rest_framework.exceptions.ValidationError` / `NotFound` in the view or a
  custom DRF exception handler)
- Never accept `request`; pass the user/ids/data the service needs
- Add Google-style docstrings with `Args`, `Returns`, `Raises`

---

## 3. QuerySets and Managers

Put reusable filters on a custom QuerySet, exposed as the default manager.

```python
# projects/models.py (excerpt)
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models


class ProjectQuerySet(models.QuerySet["Project"]):
    def active(self) -> "ProjectQuerySet":
        return self.filter(is_active=True)

    def owned_by(self, user: AbstractBaseUser) -> "ProjectQuerySet":
        return self.filter(owner=user)

    def with_task_counts(self) -> "ProjectQuerySet":
        return self.annotate(task_count=models.Count("tasks"))


class Project(models.Model):
    ...
    objects = ProjectQuerySet.as_manager()
```

```python
# CORRECT - one query for projects + owners, one for all their tasks
projects = (
    Project.objects.active()
    .select_related("owner")          # FK / one-to-one: SQL JOIN
    .prefetch_related("tasks")        # reverse FK / M2M: one extra query
    .only("id", "name", "owner__username")
)

# CORRECT - narrow a prefetch
from django.db.models import Prefetch

projects = Project.objects.prefetch_related(
    Prefetch("tasks", queryset=Task.objects.filter(done=False), to_attr="open_tasks")
)

# WRONG - N+1: one query per project for owner and tasks
for project in Project.objects.all():
    print(project.owner.username, project.tasks.count())
```

### QuerySet Rules

- `select_related()` for FK/one-to-one you read; `prefetch_related()` for reverse FK/M2M
- Aggregate in the database (`annotate`, `aggregate`, `Count`, `Sum`), not in Python
- Use `exists()` instead of `count() > 0` / truthiness; `update()` / `bulk_create()` for batches
- Use `F()` expressions for concurrent-safe increments: `.update(views=F("views") + 1)`
- Use `get_object_or_404` / DRF `get_object()` in views, never bare `.get()` on user input
- Scope every queryset by the current user/tenant in `get_queryset()`

---

## 4. Transactions

```python
from django.db import IntegrityError, transaction


@transaction.atomic
def transfer_ownership(project: Project, new_owner_id: int) -> Project:
    project.owner_id = new_owner_id
    project.save(update_fields=["owner", "updated_at"])
    AuditLog.objects.create(project=project, action="owner_changed")
    return project


# Savepoint for an expected failure inside a larger transaction
with transaction.atomic():
    try:
        with transaction.atomic():
            Tag.objects.create(name=name)
    except IntegrityError:
        tag = Tag.objects.get(name=name)
```

- Do not catch `IntegrityError` inside an atomic block without a nested savepoint
- Keep external HTTP calls out of open transactions (use `on_commit` or do them before)
- Prefer `get_or_create` / `update_or_create` with a unique constraint over check-then-insert

---

## 5. Settings and Configuration

- Read configuration from environment variables in `config/settings.py` (see
  `patterns/django-patterns.md` section 5); `os.environ["DJANGO_SECRET_KEY"]` for
  required secrets, no insecure defaults, `DEBUG` only when `DJANGO_DEBUG=1`
- Access settings with `from django.conf import settings`, never by importing
  `config.settings`
- Feature values used by services (`PAGE_SIZE`, API base URLs) are settings, not
  module constants that hide environment differences

---

## 6. Service Tests

```python
# projects/tests/test_services.py
from unittest.mock import Mock

import pytest

from projects.exceptions import ProjectAlreadyArchivedError
from projects.services.project_archive import ProjectArchiveService

pytestmark = pytest.mark.django_db(transaction=True)  # on_commit callbacks run


class TestProjectArchiveService:
    def test_archives_active_project(self, project_factory) -> None:
        notifier = Mock()
        project = ProjectArchiveService(notifier=notifier).execute(project_factory())

        assert project.is_active is False
        notifier.project_archived.assert_called_once_with(project.pk)

    def test_rejects_already_archived(self, project_factory) -> None:
        with pytest.raises(ProjectAlreadyArchivedError):
            ProjectArchiveService(notifier=Mock()).execute(project_factory(is_active=False))
```

- Use `pytest.mark.django_db`; add `transaction=True` (or
  `django_capture_on_commit_callbacks`) when asserting `on_commit` side effects
- Use `django_assert_num_queries` to lock in query counts for list endpoints
- Fake collaborators through the constructor instead of patching module globals

---

## 7. Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Archived project %s", project.pk)   # %-style, lazy
logger.exception("Failed to notify project %s", project.pk)  # inside except
```

- Module-level `logging.getLogger(__name__)`; configure handlers in `LOGGING` settings
- Never log secrets, tokens or PII
