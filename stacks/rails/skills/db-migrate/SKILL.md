---
name: db-migrate
description: Create and run Rails database migrations safely with rollback verification
---

# /db-migrate

## What This Does

Creates a new database migration, runs it, and verifies it can be rolled back safely.
This ensures all migrations are reversible and the schema stays consistent.

## Usage

```
/db-migrate AddRoleToProfiles           # Generate and run a migration
/db-migrate CreateExperiences           # Generate a create table migration
/db-migrate --run                       # Run all pending migrations
/db-migrate --rollback                  # Roll back the last migration
/db-migrate --status                    # Show migration status
```

## How It Works

1. **Generate the migration.** Based on the migration name and context, generate
   an appropriate migration file:

   ```bash
   bundle exec rails generate migration <MigrationName>
   ```

2. **Edit the migration.** Open the generated migration file and add the appropriate
   schema changes based on the naming convention and user instructions:
   - `AddXToY` - adds columns to existing table
   - `RemoveXFromY` - removes columns from existing table
   - `CreateX` - creates a new table
   - `AddIndexToX` - adds indices

3. **Run the migration.**

   ```bash
   rails db:migrate
   ```

4. **Verify rollback.** Immediately test that the migration is reversible:

   ```bash
   rails db:rollback STEP=1
   ```

5. **Re-run the migration.** Apply the migration again after successful rollback:

   ```bash
   rails db:migrate
   ```

6. **Verify schema.** Check that `db/schema.rb` reflects the expected changes.

7. **Report results.**

   ```markdown
   ## Migration Results

   **Migration:** db/migrate/YYYYMMDDHHMMSS_migration_name.rb
   **Status:** SUCCESS | FAILED
   **Forward:** Applied successfully
   **Rollback:** Reversible (verified)
   **Schema:** Updated correctly
   ```

## Safety Rules

- **Always verify rollback.** Every migration must be reversible unless there is
  an explicit reason it cannot be (documented in a comment).
- **Never drop columns in production** without a two-step process:
  1. First migration: ignore the column (`self.ignored_columns`)
  2. Second migration (after deploy): drop the column
- **Add indices concurrently** for large tables using `disable_ddl_transaction!`
  and `algorithm: :concurrently`.
- **Set NOT NULL with a default** to avoid locking issues on large tables.
- **Use `change` method** (not `up`/`down`) whenever possible for automatic
  reversibility.

## Error Handling

- If the migration fails, report the error and do NOT leave the database in a
  partially migrated state. Run `rails db:rollback` if needed.
- If rollback fails, flag this as a BLOCKER and report that the migration is not
  safely reversible.
- If `db/schema.rb` has conflicts, report them for manual resolution.
