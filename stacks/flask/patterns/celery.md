# Background Jobs: Celery With the Flask App Context

Read when work must leave the request (emails, webhooks, exports) or run on a
schedule. Tasks use Flask-SQLAlchemy and config, which need an app context:
every task runs inside one. This follows the Flask docs' Celery pattern.

## Setup

Dependency: `celery[redis]`.

```python
# src/app/celery_app.py
from celery import Celery, Task
from flask import Flask


def celery_init_app(app: Flask) -> Celery:
    """Create the Celery app bound to this Flask app."""

    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
```

```python
# src/app/__init__.py (in create_app, after config is loaded)
app.config.setdefault(
    "CELERY",
    {
        "broker_url": os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        "task_ignore_result": True,
        "task_acks_late": True,
        "worker_prefetch_multiplier": 1,
    },
)
celery_init_app(app)
```

```python
# src/app/make_celery.py  (worker entry point)
from app import create_app

flask_app = create_app()
celery_app = flask_app.extensions["celery"]
```

```bash
uv run celery -A app.make_celery worker -l info
uv run celery -A app.make_celery beat -l info   # one beat per environment
```

Testing config: `CELERY={"task_always_eager": True, "broker_url": "memory://"}`.

## Task Pattern

```python
# src/app/tasks/exports.py
from celery import shared_task

from app.services.export_service import ExportService


@shared_task(
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    max_retries=5,
)
def export_project(project_id: int) -> None:
    """Export a project; the service does the work."""
    ExportService().export(project_id)
```

Use `@shared_task` (not `@celery_app.task`) so task modules do not import the
Celery instance and create import cycles with the factory.

## Rules

- Pass ids and JSON values, never model instances or the session.
- Enqueue after the commit that created the data: commit first, then `.delay()`.
  Enqueuing before the commit lets the worker read a row that does not exist yet.
- Tasks are idempotent (acks_late + retries can run them twice).
- The task body calls a service; unit-test the service, and test the task by
  calling it directly (`export_project(project.id)`) inside the app fixture.
- Never call `.get()` on a result inside a request or another task (deadlocks,
  blocked workers).

## Periodic Tasks

```python
app.config["CELERY"]["beat_schedule"] = {
    "nightly-cleanup": {
        "task": "app.tasks.maintenance.cleanup_expired",
        "schedule": crontab(hour=3, minute=0),
    },
}
```

Periodic tasks process "everything due" rather than "the last 24 hours", so a
missed run catches up.
