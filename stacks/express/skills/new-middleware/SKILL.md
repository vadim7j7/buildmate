---
name: new-middleware
description: Generate an Express middleware function
---

# /new-middleware

## What This Does

Generates an Express middleware function with proper TypeScript types and a test file.

## Usage

```
/new-middleware rate-limit     # Creates middleware/rate-limit.ts
/new-middleware cors           # Creates middleware/cors.ts
/new-middleware request-logger # Creates middleware/request-logger.ts
```

## How It Works

1. **Read reference patterns** from `patterns/express-patterns.md` and `styles/typescript.md`
2. **Generate middleware** with proper `(req, res, next)` signature
3. **Generate test file** for the middleware
4. **Run quality checks**: `npx tsc --noEmit && npm run lint && npm test`

## Generated Files

```
src/middleware/<name>.ts
src/__tests__/middleware/<name>.test.ts
```
