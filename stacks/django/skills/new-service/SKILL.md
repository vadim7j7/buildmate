---
name: new-service
description: Generate a Django service class with business logic
---

# /new-service

## What This Does

Generates a service class encapsulating business logic, keeping views thin.
Also generates the corresponding test file.

## Usage

```
/new-service ArticlePublish          # Creates ArticlePublishService
/new-service UserRegistration        # Creates UserRegistrationService
/new-service OrderProcessing         # Creates OrderProcessingService
```

## How It Works

1. **Read reference patterns.** Load the service pattern from:
   - `patterns/backend-patterns.md` — section "2. Service Pattern" (plus
     "3. QuerySets and Managers" and "4. Transactions")
   - `patterns/django-patterns.md` — project layout
   - `styles/backend-python.md`

2. **Determine service name.** Parse the argument to determine the class name:
   - `ArticlePublish` becomes `ArticlePublishService` in `<app>/services/article_publish.py`

3. **Generate the service file.** Create the service with:
   - Type annotations on all methods
   - Constructor with dependency injection
   - Main `execute()` method (sync `def`)
   - Private helper methods
   - Domain exceptions in `<app>/exceptions.py`
   - `transaction.atomic()` around multi-write operations; side effects in
     `transaction.on_commit(...)`
   - Docstrings

4. **Generate the test file.** Create the test with:
   - Tests for the happy path
   - Tests for edge cases and error conditions
   - Mocking external dependencies with `unittest.mock` or `pytest-mock`

5. **Run quality checks.**

   ```bash
   uv run ruff format <generated_files>
   uv run ruff check <generated_files>
   uv run pytest <test_file> -v
   ```

## Generated Files

```
<app>/services/<service_name>.py
<app>/tests/test_services.py  (created or updated)
```
