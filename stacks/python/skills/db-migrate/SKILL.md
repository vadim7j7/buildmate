---
name: db-migrate
description: Run database migrations safely with rollback verification
---

# /db-migrate

## What This Does

Runs pending database migrations and verifies they can be rolled back safely.
This is the generic Python version — framework children (Django, Flask, FastAPI)
override with their own conventions.

## Usage

```
/db-migrate                        # Run all pending migrations
/db-migrate --rollback             # Roll back the last migration
/db-migrate --status               # Show migration status
```

## How It Works

1. **Detect the migration tool.** Check for:
   - `alembic` → Alembic (Flask, FastAPI)
   - `django` → Django migrations

2. **Check migration status.**

   For Alembic:
   ```bash
   uv run alembic current
   uv run alembic history
   ```

   For Django:
   ```bash
   uv run python manage.py showmigrations
   ```

3. **Run the migration.**

   For Alembic:
   ```bash
   uv run alembic upgrade head
   ```

   For Django:
   ```bash
   uv run python manage.py migrate
   ```

4. **Verify rollback.** Test that the migration is reversible:

   For Alembic:
   ```bash
   uv run alembic downgrade -1
   uv run alembic upgrade head
   ```

   For Django:
   ```bash
   uv run python manage.py migrate <app> <previous_migration>
   uv run python manage.py migrate
   ```

5. **Report results.**

## Safety Rules

- **Always verify rollback.** Every migration must be reversible.
- **Never drop columns in production** without a two-step process.
- **Test on a copy of the database** when possible.

## Error Handling

- If the migration fails, report the error and suggest manual resolution.
- If rollback fails, flag as a BLOCKER and report the migration is not reversible.
