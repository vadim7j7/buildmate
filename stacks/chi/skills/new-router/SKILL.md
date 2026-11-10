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

   **Entry point.** If `cmd/server/main.go` does not exist yet, create it (see the
   *Server Entry Point* pattern in the backend-developer agent): read `PORT`
   (default `8080`), register `GET /health` returning `200` JSON, and shut down
   gracefully with `signal.NotifyContext` + `Shutdown`. Details: `r.Get("/health", ...)` writing `200` `{"status":"ok"}`, router served by `http.Server` with `ReadHeaderTimeout`.
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
