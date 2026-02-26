---
name: new-handler
description: Generate a Gin handler with request/response types and tests
---

# /new-handler

## What This Does

Generates a Gin handler struct with methods for specific operations, along with
request/response types and a test file.

## Usage

```
/new-handler auth             # Creates auth handler (login, register, logout)
/new-handler upload            # Creates file upload handler
/new-handler webhook           # Creates webhook handler
```

## How It Works

1. **Read reference patterns.** Load patterns from:
   - `patterns/gin-patterns.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-go.md`

2. **Determine handler name.** Parse the argument to determine struct name,
   file paths, and methods.

3. **Generate the handler file.** Create the handler struct with:
   - Constructor function `NewXxxHandler`
   - Service dependency injection
   - Request/response type definitions with binding tags
   - Methods for each operation

4. **Generate the test file.** Create table-driven tests with:
   - `httptest.NewRecorder()` for response capture
   - Gin test mode setup
   - Mock service injection

5. **Run quality checks.**

   ```bash
   gofmt -w <generated_files>
   golangci-lint run ./...
   go test ./...
   ```

6. **Report results.**

## Generated Files

```
internal/handler/<name>.go
internal/handler/<name>_test.go
```
