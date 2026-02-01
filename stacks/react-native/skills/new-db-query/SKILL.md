---
name: new-db-query
description: Generate Drizzle ORM query functions for database operations
---

# /new-db-query -- Generate Drizzle ORM Query Functions

## What This Does

Generates a Drizzle ORM query module with typed functions for CRUD operations
on a database table. Query functions are plain async functions designed to be
called from React Query hooks.

## Usage

```
/new-db-query getTransactions    # db/queries/transactions.ts
/new-db-query getBudgets         # db/queries/budgets.ts
/new-db-query getCategories      # db/queries/categories.ts
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name`   | Yes      | Primary function name (e.g., `getTransactions`) |

The entity name is derived from the function name by removing the `get` prefix
and converting to lowercase.

## How It Works

### 1. Determine File Location

Place the query module at:
```
db/queries/<entity>.ts
```

### 2. Check for Schema

Look for the table definition in `db/schema.ts`. If the table does not exist,
inform the user it needs to be added first.

### 3. Generate Query Functions

Create the module with:
- `get<Entity>s()` -- fetch all records (with ordering)
- `get<Entity>ById(id)` -- fetch a single record
- `create<Entity>(data)` -- insert a new record
- `update<Entity>(data)` -- update an existing record
- `delete<Entity>(id)` -- delete a record
- Optional filtered queries based on common use cases

See `references/db-query-examples.md` for templates.

### 4. Verify

```bash
npx tsc --noEmit
```

## Query Conventions

### Location

All database query functions MUST live in `db/queries/`. They must NOT be defined
inside React Query hooks, components, or stores.

### Function Signature

- Functions are plain `async` functions (not hooks)
- Accept typed parameters
- Return typed results (inferred from Drizzle schema)
- Handle single-item queries returning `T | null` (not throwing)

### Ordering

Default ordering should be `desc(createdAt)` for most entities.

### Imports

```typescript
import { eq, desc, and, or, like, gte, lte, sql } from 'drizzle-orm';
import { db } from '../client';
import { tableName, type NewTableType } from '../schema';
```
