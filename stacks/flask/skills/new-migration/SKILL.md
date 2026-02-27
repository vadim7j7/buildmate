---
name: new-migration
description: Generate a Flask-Migrate (Alembic) migration file
---

# /new-migration

## What This Does

Generates a new Flask-Migrate migration file, either by auto-detecting model
changes or from a manual description.

## Usage

```
/new-migration "add role column to users"       # Manual description
/new-migration --autogenerate                    # Auto-detect model changes
```

## How It Works

1. **Generate the migration file.**

   ```bash
   # Auto-detect model changes
   uv run flask db migrate -m "<description>"

   # Or create empty migration
   uv run flask db revision -m "<description>"
   ```

2. **Review the generated migration.** Open the file and verify:
   - `upgrade()` contains the expected schema changes
   - `downgrade()` correctly reverses all changes
   - Index names are explicit

3. **Edit if needed.** For manual migrations, add the `op.*` calls.

4. **Run quality checks.**

   ```bash
   uv run ruff format <migration_file>
   uv run ruff check <migration_file>
   ```

## Generated Files

```
migrations/versions/<timestamp>_<description>.py
```
