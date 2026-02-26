---
name: new-controller
description: Generate an Express controller class with handler methods
---

# /new-controller

## What This Does

Generates an Express controller class with CRUD handler methods that delegate to a service.

## Usage

```
/new-controller projects     # Creates controllers/project-controller.ts
/new-controller users        # Creates controllers/user-controller.ts
```

## How It Works

1. **Read reference patterns** from `patterns/express-patterns.md` and `styles/typescript.md`
2. **Generate controller** with arrow function handlers
3. **Generate or update service** if it doesn't exist
4. **Generate test file** for the controller
5. **Run quality checks**: `npx tsc --noEmit && npm run lint && npm test`

## Generated Files

```
src/controllers/<resource>-controller.ts
src/services/<resource>-service.ts (if not exists)
src/__tests__/controllers/<resource>-controller.test.ts
```
