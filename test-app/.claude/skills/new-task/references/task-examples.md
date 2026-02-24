# Celery Task Examples

Patterns for Celery tasks with retry configuration, error handling, and logging.

---

## Example 1: Basic Task with Retry

```python
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_external_data(self, resource_id: int) -> dict:
    """Sync external data for a resource.

    Args:
        resource_id: The ID of the resource to sync.

    Returns:
        Status dict with result information.
    """
    logger.info("Starting sync for resource %d", resource_id)
    try:
        # Perform the sync logic
        result = {"status": "ok", "resource_id": resource_id}
        logger.info("Sync completed for resource %d", resource_id)
        return result
    except Exception as exc:
        logger.exception("Sync failed for resource %d", resource_id)
        raise self.retry(exc=exc)
```

---

## Example 2: Email Notification Task

```python
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification_email(
    self, user_id: int, subject: str, body: str
) -> dict:
    """Send a notification email to a user.

    Args:
        user_id: The recipient user ID.
        subject: Email subject line.
        body: Email body content.

    Returns:
        Status dict with delivery information.
    """
    logger.info("Sending email to user %d: %s", user_id, subject)
    try:
        # Email sending logic here
        # e.g., use an email service client
        return {
            "status": "sent",
            "user_id": user_id,
            "subject": subject,
        }
    except ConnectionError as exc:
        logger.warning(
            "Email delivery failed for user %d, retrying...", user_id
        )
        raise self.retry(exc=exc)
    except Exception:
        logger.exception("Unexpected error sending email to user %d", user_id)
        return {"status": "failed", "user_id": user_id}
```

---

## Example 3: Batch Processing Task

```python
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def process_csv_import(self, import_id: int) -> dict:
    """Process a CSV import job.

    Args:
        import_id: The import job ID.

    Returns:
        Status dict with processing results.
    """
    logger.info("Processing import %d", import_id)

    processed = 0
    errors = []

    try:
        # Batch processing logic
        # for row in csv_rows:
        #     try:
        #         process_row(row)
        #         processed += 1
        #     except ValueError as e:
        #         errors.append(str(e))

        result = {
            "status": "complete",
            "import_id": import_id,
            "processed": processed,
            "errors": errors,
        }
        logger.info(
            "Import %d complete: %d processed, %d errors",
            import_id,
            processed,
            len(errors),
        )
        return result

    except Exception as exc:
        logger.exception("Import %d failed", import_id)
        raise self.retry(exc=exc)
```

---

## Example 4: Periodic Task

```python
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_sessions() -> dict:
    """Clean up expired user sessions.

    This task runs periodically via Celery Beat.

    Returns:
        Status dict with cleanup results.
    """
    logger.info("Starting expired session cleanup")
    # Cleanup logic
    deleted_count = 0
    return {"status": "ok", "deleted": deleted_count}
```

---

## Celery Configuration

```python
# src/app/celery_app.py
from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "app",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks in the tasks/ directory
celery_app.autodiscover_tasks(["app.tasks"])
```

---

## Test Patterns

```python
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.tasks.sync_external_data import sync_external_data


class TestSyncExternalData:
    """Tests for the sync_external_data task."""

    def test_successful_sync(self) -> None:
        result = sync_external_data(resource_id=42)
        assert result["status"] == "ok"
        assert result["resource_id"] == 42

    def test_retry_on_failure(self) -> None:
        task = sync_external_data
        task.bind = True

        # Mock self.retry
        mock_self = MagicMock()
        mock_self.retry.side_effect = Exception("Retry")

        # Verify retry is called on failure
        with patch.object(task, "retry", side_effect=Exception("Retry")):
            ...
```

---

## Key Rules

1. **Use `@shared_task(bind=True)`** for access to `self.retry()`
2. **Configure `max_retries`** and `default_retry_delay`
3. **Use `logging`** for task progress and errors (never `print()`)
4. **Return a status dict** for monitoring and debugging
5. **Catch specific exceptions** for retry vs. non-retryable errors
6. **Use `self.retry(exc=exc)`** to preserve the exception chain
7. **Add Google-style docstrings** with Args and Returns
8. **Keep tasks small** and delegate complex logic to services
