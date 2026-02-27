---
name: db-migrate
description: Create and run Django database migrations safely with rollback verification
---

# /db-migrate

## What This Does

Creates a new Django migration, runs it, and verifies it can be rolled back safely.
Ensures all migrations are reversible and the schema stays consistent.

## Usage

```
/db-migrate                                   # Generate and run pending migrations
/db-migrate --empty "backfill user roles"     # Create and run a data migration
/db-migrate --run                             # Run all pending migrations
/db-migrate --rollback                        # Roll back the last migration
/db-migrate --status                          # Show migration status
```

## How It Works

1. **Check migration status.**

   ```bash
   uv run python manage.py showmigrations
   ```

2. **Generate the migration.**

   ```bash
   # Auto-detect model changes
   uv run python manage.py makemigrations

   # Or empty for data migrations
   uv run python manage.py makemigrations <app> --empty -n <description>
   ```

3. **Review the migration.** Open the generated migration file and verify:
   - The `operations` list contains the expected schema changes
   - `dependencies` are correct
   - Data migrations have both forward and backward functions

4. **Run the migration.**

   ```bash
   uv run python manage.py migrate
   ```

5. **Verify rollback.** Test that the migration is reversible:

   ```bash
   uv run python manage.py migrate <app> <previous_migration_number>
   ```

6. **Re-run the migration.** Apply the migration again after successful rollback:

   ```bash
   uv run python manage.py migrate
   ```

7. **Report results.**

   ```markdown
   ## Migration Results

   **Migration:** <app>/migrations/NNNN_<description>.py
   **Status:** SUCCESS | FAILED
   **Forward:** Applied successfully
   **Rollback:** Reversible (verified)
   ```

## Safety Rules

- **Always verify rollback.** Every migration must be reversible.
- **Never drop columns in production** without a two-step process:
  1. First migration: stop using the column in application code
  2. Second migration (after deploy): drop the column
- **Use `RunSQL` with `reverse_sql`** for raw SQL operations.
- **Use `SeparateDatabaseAndState`** for complex operations that need custom rollback.
- **Add database indices** using `AddIndex` operation.

## Error Handling

- If the migration fails, report the error and suggest `uv run python manage.py migrate --fake` only as a last resort.
- If rollback fails, flag as a BLOCKER and report the migration is not reversible.
- If there are conflicting migrations, run `uv run python manage.py makemigrations --merge`.
