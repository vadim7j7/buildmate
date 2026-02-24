---
name: new-model
description: Generate a SQLAlchemy 2.0 model with Mapped annotations
---

# /new-model

## What This Does

Generates a SQLAlchemy 2.0 model module using `Mapped[]` type annotations, proper
table naming, and standard timestamp columns. Optionally generates an Alembic migration.

## Usage

```
/new-model project                 # Creates models/project.py
/new-model user                    # Creates models/user.py
/new-model blog_post               # Creates models/blog_post.py
/new-model task --with-migration   # Creates model + Alembic migration
```

## How It Works

1. **Read reference patterns.** Load the model pattern from:
   - `skills/new-model/references/model-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-python.md`

2. **Determine model name.** Parse the argument to determine the class name and
   table name:
   - `project` becomes `Project` class, `projects` table
   - `blog_post` becomes `BlogPost` class, `blog_posts` table

3. **Generate the model file.** Create the model with:
   - `from __future__ import annotations`
   - `Base` import from `app.database`
   - `Mapped[]` type annotations for all columns
   - `mapped_column()` for column definitions
   - `__tablename__` explicit table name
   - Standard `id`, `created_at`, `updated_at` columns
   - Docstring on the class

4. **Generate migration (if `--with-migration`).** Run:

   ```bash
   uv run alembic revision --autogenerate -m "create <table_name> table"
   ```

5. **Run quality checks.**

   ```bash
   uv run ruff format src/app/models/<resource>.py
   uv run ruff check src/app/models/<resource>.py
   uv run mypy src/app/models/<resource>.py
   ```

6. **Report results.** Show the generated files.

## Generated Files

```
src/app/models/<resource>.py
alembic/versions/<timestamp>_create_<table>.py  (if --with-migration)
```
