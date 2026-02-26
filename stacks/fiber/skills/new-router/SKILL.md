---
name: new-router
description: Generate a Fiber route group with CRUD handlers, service, and tests
---

# /new-router

## What This Does

Generates a Fiber route group with CRUD endpoint handlers, service interface,
repository interface, and test file.

## Usage

```
/new-router users           # Creates handler, service, repository for users
/new-router products         # Creates handler, service, repository for products
```

## How It Works

1. **Read reference patterns** from `patterns/fiber-patterns.md` and `patterns/backend-patterns.md`.
2. **Determine resource name** and file paths.
3. **Generate handler** with CRUD methods using `*fiber.Ctx`.
4. **Generate service interface and implementation.**
5. **Generate repository interface.**
6. **Generate test file** with `app.Test()`.
7. **Register routes** in the router setup.
8. **Run quality checks**: `gofmt`, `golangci-lint`, `go test`.

## Generated Files

```
internal/handler/<resource>.go
internal/service/<resource>.go
internal/repository/<resource>.go
internal/handler/<resource>_test.go
```
