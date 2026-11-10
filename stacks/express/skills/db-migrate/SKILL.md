---
name: db-migrate
description: Create, review, apply or roll forward Prisma migrations safely
---

# /db-migrate

## What This Does

Runs the Prisma Migrate workflow: create a migration from `schema.prisma` changes,
review its SQL for data loss and locking, apply it, regenerate the client, and say
how it deploys.

## Usage

```
/db-migrate add_project_status   # create + apply a migration in development
/db-migrate status               # what's applied vs pending
/db-migrate deploy               # apply pending migrations (CI / production)
```

## How It Works

1. **Check state**: `npx prisma migrate status`. If the DB has drifted from the
   migration history, stop and report; don't reset a shared database.
2. **Create** (development DB only):

   ```bash
   npx prisma migrate dev --name <snake_case_change>   # writes prisma/migrations/<ts>_<name>/migration.sql
   npx prisma generate                                  # Prisma 7: not run by migrate anymore
   ```

   To write or edit SQL before applying (data backfill, concurrent index):
   `npx prisma migrate dev --create-only --name <name>`, edit `migration.sql`, then
   `npx prisma migrate dev`.
3. **Review the SQL** and fix risky steps before committing:

   | Change | Risk | Safer path |
   |---|---|---|
   | Drop column / table | data loss; old code still reads it | stop using it in code first, drop in a later release |
   | Rename column | Prisma emits drop + add (data loss) | edit SQL to `ALTER TABLE ... RENAME COLUMN`, or add new + backfill + drop later |
   | Add NOT NULL column without default | fails on existing rows | add nullable → backfill → set NOT NULL |
   | Change column type | rewrite + lock, may fail | new column + backfill + switch |
   | `CREATE INDEX` on a big table | blocks writes | `CREATE INDEX CONCURRENTLY` in its own migration (create-only, edit SQL) |
   | New unique constraint | fails on duplicates | dedupe first |

   The API deploys while old instances still run: every migration must work with
   the code before **and** after it.
4. **Apply elsewhere**: CI and production run `npx prisma migrate deploy` (applies
   pending migrations, never generates or resets). It reads the URL from
   `prisma.config.ts`; seed explicitly with `npx prisma db seed` if needed.
5. **Verify**: `npx prisma migrate status` clean, `npx tsc --noEmit`, `npm test`.

## Fixing Mistakes

- Migration not yet shared: `npx prisma migrate reset` (local DB only: it drops all
  data), fix the schema, create it again.
- Migration already applied somewhere shared: never edit or delete it; write a new
  migration that corrects it.
- Failed migration in production: `npx prisma migrate resolve --rolled-back <name>`
  (after undoing partial changes) or `--applied <name>` (if fixed by hand), then deploy again.

## Rules

- Commit `schema.prisma` and the migration folder together, in the same change as the code.
- No `prisma db push` for shipped changes (no migration file).
- Never point `migrate dev` / `migrate reset` at a shared or production database.
