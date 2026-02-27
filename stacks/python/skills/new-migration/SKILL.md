---
name: new-migration
description: Generate a database migration file
---

# /new-migration

## What This Does

Generates a new database migration file using the project's migration tool (Alembic,
Django migrations, or manual SQL). This is the generic Python version — framework
children (Django, Flask, FastAPI) override with their own conventions.

## Usage

```
/new-migration                                 # Auto-detect model changes
/new-migration --empty "backfill user roles"   # Empty migration for custom operations
```

## How It Works

1. **Detect the migration tool.** Check for:
   - `alembic` → Alembic migrations (Flask, FastAPI)
   - `django` → Django migrations
   - Otherwise → manual SQL migrations

2. **Generate the migration file.**

   For Alembic:
   ```bash
   uv run alembic revision --autogenerate -m "description"
   ```

   For Django:
   ```bash
   uv run python manage.py makemigrations
   ```

3. **Review the generated migration.** Open the file and verify:
   - Operations are correct
   - Dependencies are correct
   - Both `upgrade()` and `downgrade()` are implemented

4. **Run quality checks.**

   ```bash
   uv run ruff format <migration_file>
   uv run ruff check <migration_file>
   ```

## Generated Files

```
migrations/versions/<revision>_<description>.py  (Alembic)
<app>/migrations/NNNN_<description>.py           (Django)
```
