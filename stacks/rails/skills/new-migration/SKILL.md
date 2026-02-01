---
name: new-migration
description: Generate a database migration with safety patterns and rollback verification
---

# /new-migration

## What This Does

Generates a new database migration following Rails conventions and safety best
practices. Supports common operations like adding columns, creating tables, adding
indices, and working with JSONB columns.

## Usage

```
/new-migration AddRoleToProfiles              # Add a column
/new-migration CreateExperiences              # Create a new table
/new-migration AddIndexToProfilesEmail        # Add an index
/new-migration AddMetadataToCompanies         # Add JSONB column
/new-migration RemoveBioFromProfiles          # Remove a column
```

## How It Works

1. **Read reference patterns.** Load migration patterns from:
   - `skills/new-migration/references/migration-examples.md`
   - `patterns/backend-patterns.md`

2. **Generate the migration file.**

   ```bash
   bundle exec rails generate migration <MigrationName>
   ```

3. **Edit the migration.** Based on the naming convention and user instructions,
   add the appropriate schema changes:
   - `AddXToY` - `add_column` with type, default, null constraint
   - `RemoveXFromY` - `remove_column` (reversible)
   - `CreateX` - `create_table` with columns and indices
   - `AddIndexToX` - `add_index` with uniqueness/conditional options

4. **Apply safety patterns.**
   - Add `null: false` with defaults for new required columns
   - Add indices for foreign keys and frequently queried columns
   - Use `algorithm: :concurrently` for large table indices
   - Include `disable_ddl_transaction!` when using concurrent indices

5. **Run and verify.**

   ```bash
   rails db:migrate
   rails db:rollback STEP=1
   rails db:migrate
   ```

6. **Report results.**

   ```markdown
   ## Migration Results

   **File:** db/migrate/YYYYMMDDHHMMSS_migration_name.rb
   **Forward:** Applied successfully
   **Rollback:** Verified reversible
   **Schema:** Updated correctly
   ```

## Generated Files

```
db/migrate/YYYYMMDDHHMMSS_<migration_name>.rb
```
