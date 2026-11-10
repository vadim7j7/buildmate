---
name: new-test
description: Write table-driven app.Test tests for a Fiber handler or middleware
---

# /new-test

## What This Does

Writes tests for an existing Fiber v3 handler, middleware or service: table-driven
cases that send `*http.Request`s through a real `fiber.App` with `app.Test`, with a fake
service behind it.

## Usage

```
/new-test internal/handler/user.go          # handler tests
/new-test internal/middleware/auth.go       # middleware tests
/new-test UserService.CreateUser            # service unit test
```

## How It Works

1. **Read** `.claude/patterns/testing.md`, `.claude/patterns/fiber-patterns.md` and the
   code under test. Reuse fakes and helpers from existing `*_test.go` files.
2. **List the cases**: success, each validation failure, not found, unauthorized or
   forbidden (protected routes), service error -> 500 with the fixed message.
3. **Write the test** next to the file. Build the app with the same `fiber.Config`
   as production (`ErrorHandler`, `StructValidator`), or validation and error mapping
   are not tested:

```go
func newTestApp(svc service.UserService) *fiber.App {
	app := fiber.New(fiber.Config{
		ErrorHandler:    ErrorHandler,
		StructValidator: structValidator{v: validator.New()},
	})
	h := NewUserHandler(svc)
	app.Post("/users", h.Create)
	app.Get("/users/:id", h.Get)
	return app
}

func TestUserHandler_Get(t *testing.T) {
	tests := []struct {
		name       string
		id         string
		svcErr     error
		wantStatus int
	}{
		{name: "found", id: "1", wantStatus: fiber.StatusOK},
		{name: "not found", id: "2", svcErr: apperror.ErrNotFound, wantStatus: fiber.StatusNotFound},
		{name: "service fails", id: "1", svcErr: errors.New("db down"), wantStatus: fiber.StatusInternalServerError},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			app := newTestApp(&fakeUserService{err: tt.svcErr})

			req := httptest.NewRequest(http.MethodGet, "/users/"+tt.id, nil)
			resp, err := app.Test(req)
			require.NoError(t, err)
			defer resp.Body.Close()

			require.Equal(t, tt.wantStatus, resp.StatusCode)
			body, err := io.ReadAll(resp.Body)
			require.NoError(t, err)
			assert.NotContains(t, string(body), "db down") // no internal error text
		})
	}
}
```

   `app.Test` times out after 1 second by default; for slow handlers pass
   `fiber.TestConfig{Timeout: 5 * time.Second, FailOnTimeout: true}`.
   For JSON bodies use `strings.NewReader(body)` and set
   `req.Header.Set("Content-Type", "application/json")`.
   Middleware: mount it with a stub handler (`app.Get("/x", mw, func(c fiber.Ctx) error { return c.SendStatus(fiber.StatusOK) })`)
   and assert the blocked and the passing request.
4. **Run** `go test -race ./internal/handler/...`, then the quality gates.

## Rules

- Go through `app.Test`, never call a handler with a hand-built `fiber.Ctx`
- Assert status and error `code`, not full error strings
- Database-backed tests use testcontainers-go (`testing.md`)
