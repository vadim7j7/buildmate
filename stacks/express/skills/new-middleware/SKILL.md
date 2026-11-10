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

1. **Read reference patterns** from `.claude/patterns/express-patterns.md` and `.claude/styles/typescript.md`
2. **Generate middleware** with proper `(req, res, next)` signature; `async` middleware may throw (Express 5 forwards it to the error handler); never assign to `req.query` (read-only in Express 5), use `res.locals`
3. **Generate test file** for the middleware
4. **Run quality checks**: `npx tsc --noEmit && npm run lint && npm test`

## Generated Files

```
src/middleware/<name>.ts
src/__tests__/middleware/<name>.test.ts
```
