---
name: new-model
description: Add a Prisma model (fields, relations, indexes) and its migration to the Express API
---

# /new-model

## What This Does

Adds a model to `prisma/schema.prisma` with relations, indexes and constraints,
creates the migration (`/db-migrate`), regenerates the client, and adds the Zod
schemas for its API input.

## Usage

```
/new-model Project name:string description:text? owner:User status:enum(active,archived)
/new-model Comment body:text project:Project author:User
```

## How It Works

1. **Read** `prisma/schema.prisma`, `prisma.config.ts` and one existing model; copy
   its conventions (id type, timestamps, `@@map` table names, naming).
2. **Add the model**:

   ```prisma
   enum ProjectStatus {
     active
     archived
   }

   model Project {
     id          String        @id @default(uuid(7)) @db.Uuid
     name        String        @db.VarChar(255)
     description String?
     status      ProjectStatus @default(active)
     ownerId     String        @db.Uuid
     owner       User          @relation(fields: [ownerId], references: [id], onDelete: Cascade)
     createdAt   DateTime      @default(now())
     updatedAt   DateTime      @updatedAt

     @@index([ownerId, createdAt, id]) // matches the list query (owner scope + order)
     @@map("projects")
   }

   model User {
     // ...
     projects Project[]
   }
   ```

   - Every foreign key gets an index (Postgres doesn't add one) and an explicit
     `onDelete` (`Cascade`, `Restrict` or `SetNull`), chosen on purpose.
   - Uniqueness in the DB, not only in code: `@unique` / `@@unique([ownerId, name])`.
   - Money as `Decimal` (or integer cents), never `Float`; timestamps as `DateTime`.
   - New **required** column on an existing table: give it a `@default(...)`, or add it
     optional, backfill, then make it required in a second migration.
   - Follow the project's id style (`uuid()`, `uuid(7)`, `cuid()`, `autoincrement()`).
3. **Migrate**: `npx prisma migrate dev --name add_project` then `npx prisma generate`
   (Prisma 7 no longer generates on migrate). Read the generated SQL before keeping it
   (see `/db-migrate`).
4. **Add Zod schemas** in `src/schemas/<model>.ts`: create/update input (only fields a
   client may set: never `id`, `ownerId`, timestamps), id param, list query.
   Types for rows come from `@/generated/prisma/client`, input types from `z.infer`.
5. **Optionally** scaffold the API with `/new-router <models>`.
6. **Run**: `npx tsc --noEmit && npm run lint && npm test`

## Generated / Changed Files

```
prisma/schema.prisma
prisma/migrations/<timestamp>_add_<model>/migration.sql
src/schemas/<model>.ts
```

## Rules

- Never edit a migration that has been applied anywhere shared; add a new one.
- Never use `prisma db push` for changes that ship: it creates no migration.
- Prisma 6 projects (`prisma-client-js`, imports from `@prisma/client`) keep their
  setup; don't half-migrate to Prisma 7 inside a feature.
