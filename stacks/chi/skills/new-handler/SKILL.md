---
name: new-handler
description: Generate a Chi handler with request/response types and tests
---

# /new-handler

## What This Does

Generates a Chi handler struct using standard `http.HandlerFunc` signatures,
with request/response types and tests.

## Usage

```
/new-handler auth             # Creates auth handler (login, register)
/new-handler upload            # Creates file upload handler
```

## How It Works

1. **Read reference patterns** from `patterns/chi-patterns.md` and `patterns/backend-patterns.md`.
2. **Determine handler name** and file paths.
3. **Generate handler** with constructor, service dependency, and `http.HandlerFunc` methods.
4. **Generate test file** with chi router, `httptest`, and mock services.
5. **Run quality checks**: `gofmt`, `golangci-lint`, `go test`.

## Generated Files

```
internal/handler/<name>.go
internal/handler/<name>_test.go
```
