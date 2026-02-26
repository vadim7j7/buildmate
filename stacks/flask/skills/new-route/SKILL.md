---
name: new-route
description: Generate a Flask route with request validation and service delegation
---

# /new-route

## What This Does

Generates a new Flask route function within an existing blueprint. Includes request
validation with Pydantic, service call delegation, and error handling.

## Usage

```
/new-route projects.search          # Adds search route to projects blueprint
/new-route users.activate           # Adds activate route to users blueprint
/new-route projects.export --method POST  # Adds POST route
```

## How It Works

1. **Read reference patterns.** Load patterns from:
   - `patterns/flask-patterns.md`
   - `styles/backend-python.md`

2. **Locate the blueprint.** Find the existing blueprint file for the specified resource.

3. **Generate the route function.** Create a route with:
   - `from __future__ import annotations`
   - Route decorator (`@bp.get()`, `@bp.post()`, etc.)
   - Request body parsing with `request.get_json()` (for POST/PATCH/PUT)
   - Pydantic validation on input
   - Service call for business logic
   - Error handling (404, 422)
   - Type annotations and docstring

4. **Add to blueprint.** Append the route function to the blueprint module.

5. **Add service method.** If needed, add the corresponding method to the service class.

6. **Generate test.** Add a test case for the new route.

7. **Run quality checks.**

   ```bash
   uv run ruff format <modified_files>
   uv run ruff check <modified_files>
   uv run mypy <modified_files>
   ```

8. **Report results.** Show the modified files.

## Example Output

```python
@bp.post("/search")
async def search_projects():
    """Search projects by criteria."""
    data = ProjectSearch.model_validate(request.get_json())
    async with db.session() as session:
        service = ProjectService(session)
        results = await service.search(data)
    return jsonify([ProjectRead.model_validate(p).model_dump() for p in results])
```
