---
name: new-service
description: Generate a Go service with business logic and tests
---

# /new-service

## What This Does

Generates a Go service struct with business logic methods, dependency injection
via interfaces, and table-driven tests.

## Usage

```
/new-service User                # Creates internal/service/user_service.go
/new-service Order               # Creates internal/service/order_service.go
```

## How It Works

1. **Read reference patterns.** Load the service pattern from:
   - Existing services in `internal/service/`
   - `patterns/backend-patterns.md`
   - `styles/backend-go.md`

2. **Determine service name.** Parse the argument to determine the struct name:
   - `User` becomes `UserService` in `internal/service/user_service.go`

3. **Generate the service file.** Create the service with:
   - Constructor function `NewUserService(repo UserRepository) *UserService`
   - Repository interface dependency injection
   - CRUD methods: `List`, `GetByID`, `Create`, `Update`, `Delete`
   - Context as first parameter on all methods
   - Error wrapping with `fmt.Errorf("...: %w", err)`
   - Godoc comments

4. **Generate the test file.** Create tests with:
   - Table-driven tests for each method
   - Mock repository implementation
   - Error case coverage
   - `t.Helper()` on test helper functions

5. **Run quality checks.**

   ```bash
   gofmt -w <generated_files>
   golangci-lint run <generated_files>
   go test ./internal/service/...
   ```

## Generated Files

```
internal/service/<name>_service.go
internal/service/<name>_service_test.go
```
