---
name: new-router
description: Generate an Express router with CRUD endpoints, controller, service, and schema
---

# /new-router

## What This Does

Generates an Express router module with CRUD endpoints, along with the controller,
service, Zod schema, and test file.

## Usage

```
/new-router projects     # Creates routes/projects.ts, controllers/project-controller.ts, etc.
/new-router users         # Creates routes/users.ts, controllers/user-controller.ts, etc.
```

## How It Works

1. **Read reference patterns** from `patterns/express-patterns.md` and `styles/typescript.md`
2. **Generate router** with CRUD routes and validation middleware
3. **Generate controller** with handler methods
4. **Generate service** with database operations
5. **Generate Zod schema** for request validation
6. **Generate test file** with Supertest integration tests
7. **Register router** in `src/app.ts`
8. **Run quality checks**: `npx tsc --noEmit && npm run lint && npm test`

## Generated Files

```
src/routes/<resource>.ts
src/controllers/<resource>-controller.ts
src/services/<resource>-service.ts
src/schemas/<resource>.ts
src/__tests__/routes/<resource>.test.ts
```
