---
name: new-middleware
description: Generate a Chi middleware function with tests
---

# /new-middleware

## What This Does

Generates a Chi-compatible middleware using the standard
`func(http.Handler) http.Handler` signature, along with tests.

## Usage

```
/new-middleware auth          # Creates authentication middleware
/new-middleware rate-limiter  # Creates rate limiting middleware
```

## How It Works

1. **Read reference patterns** from `patterns/chi-patterns.md`.
2. **Determine middleware name** and file paths.
3. **Generate middleware** with `func(http.Handler) http.Handler` signature.
4. **Generate test file** using `httptest` and chi router.
5. **Run quality checks**: `gofmt`, `golangci-lint`, `go test`.

## Generated Files

```
internal/middleware/<name>.go
internal/middleware/<name>_test.go
```
