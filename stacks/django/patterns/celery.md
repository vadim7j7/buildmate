# Background Jobs: Celery + django-celery-beat

Read when work must run outside the request (emails, webhooks, exports, slow
third-party calls) or on a schedule.

## Setup

Dependencies: `celery[redis]`, `django-celery-beat` (and `django-celery-results`
only if you read task results).

```python
# config/celery.py
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()  # finds <app>/tasks.py
```

```python
# config/__init__.py
from .celery import app as celery_app

__all__ = ("celery_app",)
```

```python
# config/settings.py
CELERY_BROKER_URL = env("CELERY_BROKER_URL")  # e.g. redis://localhost:6379/0
CELERY_TASK_ACKS_LATE = True             # redeliver if a worker dies mid-task
CELERY_WORKER_PREFETCH_MULTIPLIER = 1    # fair dispatch for long tasks
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
INSTALLED_APPS += ["django_celery_beat"]
```

Run:

```bash
uv run celery -A config worker -l info
uv run celery -A config beat -l info    # exactly ONE beat process per environment
```

## Task Pattern

```python
# projects/tasks.py
import logging

from celery import shared_task

from projects.services.export import ExportService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=5,
)
def export_project(self, project_id: int) -> None:
    """Export a project; thin wrapper, logic lives in the service."""
    ExportService().export(project_id)
```

Rules:
- Arguments are ids and plain JSON values, never model instances (they are
  serialized, and stale by the time the task runs).
- Tasks are **idempotent**: with `acks_late` and retries, a task can run twice.
  Check state first (`if export.status == "done": return`) or use a unique key.
- The task body calls a service; tests cover the service directly.
- Retry only transient errors (network, 5xx, lock timeouts), not bugs.

## Enqueue After Commit

A task enqueued inside a transaction can start before the commit and not find
the row. Enqueue on commit:

```python
from django.db import transaction

with transaction.atomic():
    project = Project.objects.create(...)
    transaction.on_commit(lambda: export_project.delay(project.id))
```

Celery 5.4+ has the shortcut `export_project.delay_on_commit(project.id)` for
tasks of a Django-configured app.

## Periodic Tasks

With `DatabaseScheduler`, schedules live in the database and are editable in the
admin. Define the defaults in code with a data migration or an idempotent
management command, so every environment gets them:

```python
from django_celery_beat.models import CrontabSchedule, PeriodicTask

schedule, _ = CrontabSchedule.objects.get_or_create(
    minute="0", hour="3", day_of_week="*", day_of_month="*", month_of_year="*",
    timezone="UTC",
)
PeriodicTask.objects.update_or_create(
    name="nightly-cleanup",
    defaults={"crontab": schedule, "task": "projects.tasks.cleanup_expired"},
)
```

A periodic task must tolerate overlap (the previous run still going) and missed
runs (beat was down): process "everything due", not "the last 24 hours".

## Testing

- Unit-test the service; for the task, call it directly: `export_project(project.id)`
  (or `.apply()` to go through Celery's machinery, retries included).
- For code that enqueues, patch `.delay` and assert the call; with
  `transaction.on_commit`, use pytest-django's `django_capture_on_commit_callbacks`
  fixture (`with django_capture_on_commit_callbacks(execute=True): ...`).
- `CELERY_TASK_ALWAYS_EAGER = True` in test settings runs tasks inline; it hides
  serialization problems, so keep arguments JSON-simple anyway.

## Django 6 `django.tasks`

Django 6.0 added a built-in task API (`from django.tasks import task`,
`my_task.enqueue(...)`), but ships only development backends (immediate and
dummy) and no worker. Production use needs a third-party backend. In a project
already on Celery, keep Celery; do not mix the two for the same jobs.
