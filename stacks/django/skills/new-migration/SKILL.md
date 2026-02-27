---
name: new-migration
description: Generate a Django migration file
---

# /new-migration

## What This Does

Generates a new Django migration file, either by auto-detecting model changes or
creating an empty migration for custom data operations.

## Usage

```
/new-migration                                 # Auto-detect model changes
/new-migration --empty "backfill user roles"   # Empty migration for custom operations
/new-migration --app users                     # Generate for specific app
```

## How It Works

1. **Generate the migration file.**

   ```bash
   # Auto-detect model changes
   uv run python manage.py makemigrations

   # For a specific app
   uv run python manage.py makemigrations <app_name>

   # Empty migration for data migrations
   uv run python manage.py makemigrations <app_name> --empty -n <description>
   ```

2. **Review the generated migration.** Open the file and verify:
   - `operations` list contains the expected changes
   - `dependencies` are correct
   - For data migrations, implement both `forwards` and `backwards` functions
   - Index names are explicit where needed

3. **Edit if needed.** For empty data migrations, add the `RunPython` operations.

4. **Run quality checks.**

   ```bash
   uv run ruff format <migration_file>
   uv run ruff check <migration_file>
   ```

5. **Report results.** Show the generated migration file path and contents.

## Generated Files

```
<app>/migrations/NNNN_<description>.py
```
