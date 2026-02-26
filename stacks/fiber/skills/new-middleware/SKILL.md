---
name: new-middleware
description: Generate a Fiber middleware function with tests
---

# /new-middleware

## What This Does

Generates a Fiber middleware function returning `fiber.Handler`, along with tests.

## Usage

```
/new-middleware auth          # Creates authentication middleware
/new-middleware rate-limiter  # Creates rate limiting middleware
```

## How It Works

1. **Read reference patterns** from `patterns/fiber-patterns.md`.
2. **Determine middleware name** and file paths.
3. **Generate middleware** returning `fiber.Handler` with proper `c.Next()` / error flow.
4. **Generate test file** using `app.Test()`.
5. **Run quality checks**: `gofmt`, `golangci-lint`, `go test`.

## Generated Files

```
internal/middleware/<name>.go
internal/middleware/<name>_test.go
```
