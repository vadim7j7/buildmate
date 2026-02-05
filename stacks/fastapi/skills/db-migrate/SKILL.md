---
name: db-migrate
description: Create and run Alembic database migrations safely with rollback verification
---

# /db-migrate

## What This Does

Creates a new Alembic migration, runs it, and verifies it can be rolled back safely.
This ensures all migrations are reversible and the schema stays consistent.

## Usage

```
/db-migrate "Add role column to users"   # Generate and run a migration
/db-migrate --autogenerate               # Auto-detect model changes and generate migration
/db-migrate --run                        # Run all pending migrations
/db-migrate --rollback                   # Roll back the last migration
/db-migrate --status                     # Show migration status
```

## How It Works

1. **Generate the migration.** Based on the description or `--autogenerate` flag:

   ```bash
   # Manual migration
   uv run alembic revision -m "add role column to users"

   # Auto-detect model changes
   uv run alembic revision --autogenerate -m "add role column to users"
   ```

2. **Review the migration.** Open the generated migration file in
   `alembic/versions/` and verify:
   - The `upgrade()` function contains the expected schema changes
   - The `downgrade()` function correctly reverses the changes
   - Index names are explicit (not auto-generated)
   - Nullable/default values are appropriate

3. **Run the migration.**

   ```bash
   uv run alembic upgrade head
   ```

4. **Verify rollback.** Test that the migration is reversible:

   ```bash
   uv run alembic downgrade -1
   ```

5. **Re-run the migration.** Apply the migration again after successful rollback:

   ```bash
   uv run alembic upgrade head
   ```

6. **Verify current state.** Confirm the migration is applied:

   ```bash
   uv run alembic current
   ```

7. **Report results.**

   ```markdown
   ## Migration Results

   **Migration:** alembic/versions/abc123_add_role_column_to_users.py
   **Status:** SUCCESS | FAILED
   **Forward:** Applied successfully
   **Rollback:** Reversible (verified)
   **Current:** abc123 (head)
   ```

## Safety Rules

- **Always verify rollback.** Every migration must be reversible unless there is
  an explicit reason it cannot be (documented in a comment).
- **Never drop columns in production** without a two-step process:
  1. First migration: stop using the column in application code
  2. Second migration (after deploy): drop the column
- **Add indices concurrently** for large tables using `op.execute()` with
  `CREATE INDEX CONCURRENTLY`.
- **Set NOT NULL with a default** to avoid locking issues on large tables. Use a
  two-step migration: add column nullable, backfill, set NOT NULL.
- **Use `op.batch_alter_table()`** for SQLite compatibility during development.
- **Name constraints explicitly** for predictable rollback behavior.

## Error Handling

- If the migration fails, report the error and do NOT leave the database in a
  partially migrated state. Run `uv run alembic downgrade -1` if needed.
- If rollback fails, flag this as a BLOCKER and report that the migration is not
  safely reversible.
- If there are merge conflicts in `alembic/versions/`, run
  `uv run alembic merge heads -m "merge"` to resolve.
