---
name: new-migration
description: Generate an Alembic migration file
---

# /new-migration

## What This Does

Generates a new Alembic migration file, either by auto-detecting model changes or from
a manual description. Ensures the migration has proper upgrade and downgrade functions.

## Usage

```
/new-migration "add role column to users"       # Manual migration
/new-migration --autogenerate "add users table"  # Auto-detect from models
/new-migration "create projects table" --auto    # Short form for autogenerate
```

## How It Works

1. **Read reference patterns.** Load the migration pattern from:
   - `skills/new-migration/references/migration-examples.md`
   - `patterns/backend-patterns.md`

2. **Generate the migration file.**

   ```bash
   # Auto-detect model changes
   uv run alembic revision --autogenerate -m "<description>"

   # Or manual (empty template)
   uv run alembic revision -m "<description>"
   ```

3. **Review the generated migration.** Open the file in `alembic/versions/` and verify:
   - `upgrade()` contains the expected schema changes
   - `downgrade()` correctly reverses all changes
   - Index names are explicit
   - Nullable and default values are correct

4. **Edit if needed.** For manual migrations, add the appropriate `op.*` calls.

5. **Run quality checks.**

   ```bash
   uv run ruff format alembic/versions/<migration_file>.py
   uv run ruff check alembic/versions/<migration_file>.py
   ```

6. **Report results.** Show the generated migration file path and contents.

## Generated Files

```
alembic/versions/<timestamp>_<description>.py
```
