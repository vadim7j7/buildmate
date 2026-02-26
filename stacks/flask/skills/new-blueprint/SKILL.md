---
name: new-blueprint
description: Generate a Flask blueprint with route stubs, service, schema, and registration
---

# /new-blueprint

## What This Does

Generates a Flask blueprint module with CRUD route stubs, along with the corresponding
service class, Pydantic schemas, and a test file. Registers the blueprint in the app factory.

## Usage

```
/new-blueprint projects           # Creates blueprints/projects.py, services/project_service.py, schemas/project.py
/new-blueprint users              # Creates blueprints/users.py, services/user_service.py, schemas/user.py
/new-blueprint blog/posts         # Creates blueprints/blog/posts.py (nested path)
```

## How It Works

1. **Read reference patterns.** Load the blueprint pattern from:
   - `patterns/flask-patterns.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-python.md`

2. **Determine resource name.** Parse the argument to determine the resource name,
   file paths, and URL prefix:
   - `projects` becomes `/api/projects` prefix, `ProjectService`, `ProjectCreate`, etc.
   - `blog/posts` becomes `/api/blog/posts` prefix in `src/app/blueprints/blog/posts.py`

3. **Generate the blueprint file.** Create the blueprint with:
   - `from __future__ import annotations`
   - `Blueprint` with name
   - CRUD routes: list, create, get, update, delete
   - Pydantic validation on request bodies
   - Service delegation for business logic
   - Type annotations and docstrings

4. **Generate the service file.** Create the service class with:
   - Async methods for all CRUD operations
   - Session injection via constructor
   - Type annotations and docstrings

5. **Generate the schema file.** Create Pydantic v2 schemas:
   - `ResourceBase`, `ResourceCreate`, `ResourceUpdate`, `ResourceRead`

6. **Generate the test file.** Create pytest tests for the blueprint.

7. **Register the blueprint.** Add the blueprint import and `register_blueprint` call
   to `src/app/__init__.py` or the `register_blueprints()` function.

8. **Run quality checks.**

   ```bash
   uv run ruff format <generated_files>
   uv run ruff check <generated_files>
   uv run mypy <generated_files>
   ```

9. **Report results.** Show the generated files.

## Generated Files

```
src/app/blueprints/<resource>.py
src/app/services/<resource>_service.py
src/app/schemas/<resource>.py
tests/blueprints/test_<resource>.py
```
