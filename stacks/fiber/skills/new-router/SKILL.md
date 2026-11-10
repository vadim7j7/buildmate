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
3. **Generate handler** with CRUD methods using `c fiber.Ctx` (Fiber v3), `c.Bind().Body()`, and `strings.Clone` for any param kept past the handler.
4. **Generate service interface and implementation.**
5. **Generate repository interface.**
6. **Generate test file** with `app.Test()`.
7. **Register routes** in the router setup.

   **Entry point.** If `cmd/server/main.go` does not exist yet, create it (see the
   *Server Entry Point* pattern in the backend-developer agent): read `PORT`
   (default `8080`), register `GET /health` returning `200` JSON, and shut down
   gracefully with `signal.NotifyContext` + `Shutdown`. Details: `app.Get("/health", ...)` returning `c.JSON(fiber.Map{"status": "ok"})`, `app.Listen` in a goroutine and `app.ShutdownWithContext` on signal.
   Verification runs `PORT=8080 go run ./cmd/server` and polls `/health`.
8. **Run quality checks**: `gofmt`, `golangci-lint`, `go test`.

## Generated Files

```
internal/handler/<resource>.go
internal/service/<resource>.go
internal/repository/<resource>.go
internal/handler/<resource>_test.go
cmd/server/main.go                 # only if missing
```
