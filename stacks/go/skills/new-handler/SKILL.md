---
name: new-handler
description: Generate a Go HTTP handler with request/response types and tests
---

# /new-handler

## What This Does

Generates a Go HTTP handler with request/response structs, input validation,
and httptest-based tests.

## Usage

```
/new-handler User                # Creates internal/handler/user_handler.go
/new-handler Order               # Creates internal/handler/order_handler.go
```

## How It Works

1. **Read reference patterns.** Load the handler pattern from:
   - Existing handlers in `internal/handler/`
   - `patterns/backend-patterns.md`
   - `styles/backend-go.md`

2. **Determine handler name.** Parse the argument to determine the struct name:
   - `User` becomes `UserHandler` in `internal/handler/user_handler.go`

3. **Generate the handler file.** Create the handler with:
   - Constructor `NewUserHandler(svc UserService) *UserHandler`
   - Service dependency injection
   - Request/response structs with JSON tags
   - Handler methods: `List`, `GetByID`, `Create`, `Update`, `Delete`
   - Input validation and error responses
   - Proper HTTP status codes
   - Godoc comments

4. **Generate the test file.** Create tests with:
   - `httptest.NewRecorder()` and `httptest.NewRequest()`
   - Table-driven tests for each endpoint
   - Mock service implementation
   - JSON response validation
   - Error response tests

5. **Run quality checks.**

   ```bash
   gofmt -w <generated_files>
   golangci-lint run <generated_files>
   go test ./internal/handler/...
   ```

## Generated Files

```
internal/handler/<name>_handler.go
internal/handler/<name>_handler_test.go
```
