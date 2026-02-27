---
name: new-service
description: Generate a Python service class with business logic
---

# /new-service

## What This Does

Generates a service class encapsulating business logic, keeping views/routes thin.
Also generates the corresponding test file. This is the generic Python version —
framework children (Django, Flask, FastAPI) override with their own conventions.

## Usage

```
/new-service ArticlePublish          # Creates ArticlePublishService
/new-service UserRegistration        # Creates UserRegistrationService
```

## How It Works

1. **Read reference patterns.** Load the service pattern from:
   - `styles/backend-python.md`

2. **Determine service name.** Parse the argument to determine the class name:
   - `ArticlePublish` becomes `ArticlePublishService` in `services/article_publish.py`

3. **Generate the service file.** Create the service with:
   - Type annotations on all methods
   - Constructor with dependency injection
   - Main `execute()` or `call()` method
   - Private helper methods
   - Proper exception handling with custom exceptions
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
services/<service_name>.py  (or <app>/services/<service_name>.py)
tests/test_<service_name>.py
```
