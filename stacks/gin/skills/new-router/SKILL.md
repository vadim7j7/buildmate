---
name: new-router
description: Generate a Gin router group with CRUD handlers, service, and tests
---

# /new-router

## What This Does

Generates a Gin router group with CRUD endpoint handlers, along with the corresponding
service interface, repository interface, and test file.

## Usage

```
/new-router users           # Creates handler, service, repository for users
/new-router products         # Creates handler, service, repository for products
/new-router admin/settings   # Creates nested route group
```

## How It Works

1. **Read reference patterns.** Load patterns from:
   - `patterns/gin-patterns.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-go.md`

2. **Determine resource name.** Parse the argument to determine the resource name,
   file paths, and URL prefix.

3. **Generate the handler file.** Create the handler struct with:
   - CRUD methods: List, Get, Create, Update, Delete
   - Request binding with validation
   - Error handling via `handleError`

4. **Generate the service interface and implementation.**

5. **Generate the repository interface.**

6. **Generate the test file.** Create table-driven tests for each handler method.

7. **Register routes.** Add the route group to the router setup.

8. **Run quality checks.**

   ```bash
   gofmt -w <generated_files>
   golangci-lint run ./...
   go test ./...
   ```

9. **Report results.**

## Generated Files

```
internal/handler/<resource>.go
internal/service/<resource>.go
internal/repository/<resource>.go
internal/handler/<resource>_test.go
```
