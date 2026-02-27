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
   - `patterns/django-patterns.md`
   - `styles/backend-python.md`

2. **Determine service name.** Parse the argument to determine the class name:
   - `ArticlePublish` becomes `ArticlePublishService` in `<app>/services/article_publish.py`

3. **Generate the service file.** Create the service with:
   - Type annotations on all methods
   - Constructor with dependency injection
   - Main `execute()` or `call()` method
   - Private helper methods
   - Proper exception handling with custom exceptions
   - `@transaction.atomic` for database operations
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
