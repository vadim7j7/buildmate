---
name: new-schema
description: Generate a Pydantic v2 schema set (Base, Create, Update, Read)
---

# /new-schema

## What This Does

Generates a Pydantic v2 schema module with the standard set of schemas: Base, Create,
Update, and Read. Follows the project's schema conventions with `ConfigDict`,
type annotations, and docstrings.

## Usage

```
/new-schema project              # Creates schemas/project.py
/new-schema user                 # Creates schemas/user.py
/new-schema blog_post            # Creates schemas/blog_post.py
```

## How It Works

1. **Read reference patterns.** Load the schema pattern from:
   - `skills/new-schema/references/schema-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-python.md`

2. **Determine resource name.** Parse the argument to determine the class names:
   - `project` becomes `ProjectBase`, `ProjectCreate`, `ProjectUpdate`, `ProjectRead`
   - `blog_post` becomes `BlogPostBase`, `BlogPostCreate`, `BlogPostUpdate`, `BlogPostRead`

3. **Generate the schema file.** Create the schema module with:
   - `from __future__ import annotations`
   - `ProjectBase` with shared required fields
   - `ProjectCreate` inheriting from Base
   - `ProjectUpdate` with all optional fields
   - `ProjectRead` with `ConfigDict(from_attributes=True)` and DB fields
   - Type annotations and docstrings on all classes

4. **Run quality checks.**

   ```bash
   uv run ruff format src/app/schemas/<resource>.py
   uv run ruff check src/app/schemas/<resource>.py
   uv run mypy src/app/schemas/<resource>.py
   ```

5. **Report results.** Show the generated file.

## Generated Files

```
src/app/schemas/<resource>.py
```
