---
name: new-server-route
description: Generate Nuxt 4 server API routes with CRUD operations, validation and auth
---

# /new-server-route

## What This Does

Generates Nuxt 4 (Nitro) server API route handlers for CRUD operations on a resource,
with Zod validation and auth checks.

## Usage

```
/new-server-route projects   # Creates server/api/projects/... route files
/new-server-route users       # Creates server/api/users/... route files
```

## How It Works

1. **Read reference patterns** from `.claude/patterns/nuxt-patterns.md` and `.claude/styles/typescript.md`
2. **Generate a schema** in `shared/schemas/<resource>.ts` (Zod: input, query, params)
3. **Generate route handlers** with `defineEventHandler`:
   - `index.get.ts` - List with pagination (`getValidatedQuery(event, schema.parse)`)
   - `index.post.ts` - Create (`readValidatedBody(event, schema.parse)`)
   - `[id].get.ts` - Get by ID (`getValidatedRouterParams(event, schema.parse)`)
   - `[id].patch.ts` - Update
   - `[id].delete.ts` - Delete
   Every handler for private data calls `requireUser(event)` (from `server/utils/`) and
   scopes queries by the user, so a forged ID cannot reach other users' data.
4. **Generate tests** with `setup()` and `$fetch` / `fetch` from `@nuxt/test-utils/e2e`
   covering 401, 400 and the happy path
5. **Run quality checks**: `npx nuxi typecheck && npm run lint && npx vitest run`

## Generated Files

```
shared/schemas/<resource>.ts
server/api/<resource>/index.get.ts
server/api/<resource>/index.post.ts
server/api/<resource>/[id].get.ts
server/api/<resource>/[id].patch.ts
server/api/<resource>/[id].delete.ts
tests/e2e/<resource>.test.ts
```
