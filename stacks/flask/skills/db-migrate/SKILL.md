---
name: db-migrate
description: Create and run Flask-Migrate database migrations safely with rollback verification
---

# /db-migrate

## What This Does

Creates a new Flask-Migrate migration, runs it, and verifies it can be rolled back
safely.

## Usage

```
/db-migrate "Add role column to users"   # Generate and run a migration
/db-migrate --run                        # Run all pending migrations
/db-migrate --rollback                   # Roll back the last migration
/db-migrate --status                     # Show migration status
```

## How It Works

1. **Generate the migration.**

   ```bash
   uv run flask db migrate -m "<description>"
   ```

2. **Review the migration.** Verify `upgrade()` and `downgrade()` are correct.

3. **Run the migration.**

   ```bash
   uv run flask db upgrade
   ```

4. **Verify rollback.**

   ```bash
   uv run flask db downgrade
   ```

5. **Re-run the migration.**

   ```bash
   uv run flask db upgrade
   ```

6. **Report results.**

   ```markdown
   ## Migration Results

   **Migration:** migrations/versions/<file>.py
   **Status:** SUCCESS | FAILED
   **Forward:** Applied successfully
   **Rollback:** Reversible (verified)
   ```

## Safety Rules

- **Always verify rollback.** Every migration must be reversible.
- **Never drop columns in production** without a two-step process.
- **Use `op.batch_alter_table()`** for SQLite compatibility during development.
- **Name constraints explicitly** for predictable rollback behavior.
