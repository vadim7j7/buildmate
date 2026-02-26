---
name: new-middleware
description: Generate a Gin middleware function with tests
---

# /new-middleware

## What This Does

Generates a Gin middleware function that returns `gin.HandlerFunc`, along with
a corresponding test file.

## Usage

```
/new-middleware auth          # Creates authentication middleware
/new-middleware rate-limiter  # Creates rate limiting middleware
/new-middleware cors          # Creates CORS middleware
```

## How It Works

1. **Read reference patterns.** Load patterns from:
   - `patterns/gin-patterns.md`
   - `styles/backend-go.md`

2. **Determine middleware name.** Parse the argument to determine the function name
   and file paths.

3. **Generate the middleware file.** Create a function returning `gin.HandlerFunc` with:
   - Proper `c.Next()` / `c.Abort()` flow
   - Configuration via function parameters or options pattern
   - Context value setting with `c.Set()`

4. **Generate the test file.** Create tests using `httptest` and Gin's test mode.

5. **Run quality checks.**

   ```bash
   gofmt -w <generated_files>
   golangci-lint run ./...
   go test ./...
   ```

6. **Report results.**

## Generated Files

```
internal/middleware/<name>.go
internal/middleware/<name>_test.go
```
