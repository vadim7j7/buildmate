---
name: new-server-route
description: Generate Nuxt 3 server API routes with CRUD operations
---

# /new-server-route

## What This Does

Generates Nuxt 3 server API route handlers for CRUD operations on a resource.

## Usage

```
/new-server-route projects   # Creates server/api/projects/... route files
/new-server-route users       # Creates server/api/users/... route files
```

## How It Works

1. **Read reference patterns** from `patterns/nuxt-patterns.md` and `styles/typescript.md`
2. **Generate route handlers** with `defineEventHandler`:
   - `index.get.ts` - List with pagination
   - `index.post.ts` - Create
   - `[id].get.ts` - Get by ID
   - `[id].patch.ts` - Update
   - `[id].delete.ts` - Delete
3. **Run quality checks**: `npx tsc --noEmit && npm run lint && npx vitest run`

## Generated Files

```
server/api/<resource>/index.get.ts
server/api/<resource>/index.post.ts
server/api/<resource>/[id].get.ts
server/api/<resource>/[id].patch.ts
server/api/<resource>/[id].delete.ts
```
