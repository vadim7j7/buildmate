---
name: new-service
description: Generate a Flask service class with business logic
---

# /new-service

## What This Does

Generates a service class encapsulating business logic, keeping views/routes thin.
Also generates the corresponding test file.

## Usage

```
/new-service ArticlePublish          # Creates ArticlePublishService
/new-service UserRegistration        # Creates UserRegistrationService
```

## How It Works

1. **Read reference patterns.** Load the service pattern from:
   - `patterns/flask-patterns.md`
   - `styles/backend-python.md`

2. **Determine service name.** Parse the argument to determine the class name:
   - `ArticlePublish` becomes `ArticlePublishService` in `app/services/article_publish.py`

3. **Generate the service file.** Create the service with:
   - Type annotations on all methods
   - Constructor with dependency injection
   - Main `execute()` method
   - `db.session` usage within app context
   - Proper exception handling
   - Docstrings

4. **Generate the test file.** Create the test with:
   - Flask app context fixture
   - Tests for the happy path
   - Tests for edge cases and error conditions

5. **Run quality checks.**

   ```bash
   uv run ruff format <generated_files>
   uv run ruff check <generated_files>
   uv run pytest <test_file> -v
   ```

## Generated Files

```
app/services/<service_name>.py
tests/test_services.py  (created or updated)
```
