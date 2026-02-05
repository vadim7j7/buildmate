---
name: new-task
description: Generate a Celery task with retry configuration
---

# /new-task

## What This Does

Generates a Celery task module with the `@shared_task` decorator, retry configuration,
error handling, and a corresponding test file.

## Usage

```
/new-task sync_external_data      # Creates tasks/sync_external_data.py
/new-task send_notification       # Creates tasks/send_notification.py
/new-task process_upload          # Creates tasks/process_upload.py
```

## How It Works

1. **Read reference patterns.** Load the task pattern from:
   - `skills/new-task/references/task-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-python.md`

2. **Determine task name.** Parse the argument to determine the function name and
   file path:
   - `sync_external_data` becomes `sync_external_data()` in
     `src/app/tasks/sync_external_data.py`

3. **Generate the task file.** Create the task with:
   - `from __future__ import annotations`
   - `@shared_task(bind=True, max_retries=3, default_retry_delay=60)`
   - Error handling with `self.retry(exc=exc)`
   - Type annotations and docstring
   - Logging setup

4. **Generate the test file.** Create a test file with:
   - Tests for successful execution
   - Tests for retry behavior
   - Tests for error handling

5. **Run quality checks.**

   ```bash
   uv run ruff format <generated_files>
   uv run ruff check <generated_files>
   uv run mypy <generated_files>
   ```

6. **Report results.** Show the generated files.

## Generated Files

```
src/app/tasks/<task_name>.py
tests/tasks/test_<task_name>.py
```
