---
name: new-router
description: Generate a Chi sub-router with CRUD handlers, service, and tests
---

# /new-router

## What This Does

Generates a Chi resource router with CRUD handlers using standard `http.HandlerFunc`
signatures, along with service, repository, and test files.

## Usage

```
/new-router users           # Creates handler, service, repository for users
/new-router products         # Creates handler, service, repository for products
```

## How It Works

1. **Read reference patterns** from `patterns/chi-patterns.md` and `patterns/backend-patterns.md`.
2. **Determine resource name** and file paths.
3. **Generate handler** with CRUD methods using `http.HandlerFunc` and `chi.URLParam`.
4. **Generate service interface and implementation.**
5. **Generate repository interface.**
6. **Generate test file** using `chi.NewRouter()` with `httptest`.
7. **Mount routes** with `r.Mount()` in the main router.
8. **Run quality checks**: `gofmt`, `golangci-lint`, `go test`.

## Generated Files

```
internal/handler/<resource>.go
internal/service/<resource>.go
internal/repository/<resource>.go
internal/handler/<resource>_test.go
```
