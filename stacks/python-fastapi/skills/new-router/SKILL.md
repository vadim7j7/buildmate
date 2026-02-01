---
name: new-router
description: Generate a FastAPI router with CRUD endpoints, service, schema, and tests
---

# /new-router

## What This Does

Generates a FastAPI router module with full CRUD endpoints, along with the corresponding
service class, Pydantic schemas, and a test file.

## Usage

```
/new-router projects           # Creates routers/projects.py, services/project_service.py, schemas/project.py
/new-router users              # Creates routers/users.py, services/user_service.py, schemas/user.py
/new-router blog/posts         # Creates routers/blog/posts.py (nested path)
```

## How It Works

1. **Read reference patterns.** Load the router pattern from:
   - `skills/new-router/references/router-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-python.md`

2. **Determine resource name.** Parse the argument to determine the resource name,
   file paths, and URL prefix:
   - `projects` becomes `/projects` prefix, `ProjectService`, `ProjectCreate`, etc.
   - `blog/posts` becomes `/blog/posts` prefix in `src/app/routers/blog/posts.py`

3. **Generate the router file.** Create the router with:
   - `from __future__ import annotations`
   - `APIRouter` with prefix and tags
   - CRUD endpoints: list, create, get, update, delete
   - Dependency injection for `AsyncSession`
   - `response_model` on all endpoints
   - Type annotations and docstrings

4. **Generate the service file.** Create the service class with:
   - Async methods for all CRUD operations
   - Session injection via constructor
   - Type annotations and docstrings

5. **Generate the schema file.** Create Pydantic v2 schemas:
   - `ResourceBase`, `ResourceCreate`, `ResourceUpdate`, `ResourceRead`

6. **Generate the test file.** Create pytest tests for the router.

7. **Register the router.** Add the router import and `include_router` call to
   `src/app/main.py` if it exists.

8. **Run quality checks.**

   ```bash
   uv run ruff format <generated_files>
   uv run ruff check <generated_files>
   uv run mypy <generated_files>
   ```

9. **Report results.** Show the generated files.

## Generated Files

```
src/app/routers/<resource>.py
src/app/services/<resource>_service.py
src/app/schemas/<resource>.py
tests/routers/test_<resource>.py
```
