---
name: new-service
description: Generate an async service class with CRUD operations
---

# /new-service

## What This Does

Generates an async service class with standard CRUD operations, database session
injection, and proper type annotations. Also generates the corresponding test file.

## Usage

```
/new-service project             # Creates services/project_service.py
/new-service user                # Creates services/user_service.py
/new-service blog_post           # Creates services/blog_post_service.py
```

## How It Works

1. **Read reference patterns.** Load the service pattern from:
   - `skills/new-service/references/service-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-python.md`

2. **Determine service name.** Parse the argument to determine the class name:
   - `project` becomes `ProjectService` in `src/app/services/project_service.py`
   - `blog_post` becomes `BlogPostService` in `src/app/services/blog_post_service.py`

3. **Generate the service file.** Create the service with:
   - `from __future__ import annotations`
   - `AsyncSession` injection via constructor
   - Async CRUD methods: `list`, `get_by_id`, `create`, `update`, `delete`
   - `model_dump()` for Pydantic-to-ORM conversion
   - `model_dump(exclude_unset=True)` for partial updates
   - Type annotations and docstrings

4. **Generate the test file.** Create the spec file with:
   - Test class with async test methods
   - Tests for each CRUD operation
   - Edge cases (not found, empty list)

5. **Run quality checks.**

   ```bash
   uv run ruff format <generated_files>
   uv run ruff check <generated_files>
   uv run mypy <generated_files>
   ```

6. **Report results.** Show the generated files.

## Generated Files

```
src/app/services/<resource>_service.py
tests/services/test_<resource>_service.py
```
