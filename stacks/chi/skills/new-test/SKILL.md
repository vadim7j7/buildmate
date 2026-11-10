---
name: new-test
description: Write table-driven httptest tests for a Chi handler or middleware
---

# /new-test

## What This Does

Writes tests for an existing Chi handler, middleware or service: table-driven cases
served through a real `chi.Router` with `httptest`, with a fake service behind it.

## Usage

```
/new-test internal/handler/user.go          # handler tests
/new-test internal/middleware/auth.go       # middleware tests
/new-test UserService.CreateUser            # service unit test
```

## How It Works

1. **Read** `.claude/patterns/testing.md`, `.claude/patterns/chi-patterns.md` and the
   code under test. Reuse fakes and helpers from existing `*_test.go` files.
2. **List the cases**: success, each validation failure, not found, unauthorized or
   forbidden (protected routes), service error -> 500 with the fixed message.
3. **Write the test** next to the file. Mount the handler on a router so
   `chi.URLParam` works:

```go
func TestUserHandler_Get(t *testing.T) {
	tests := []struct {
		name       string
		id         string
		svcErr     error
		wantStatus int
	}{
		{name: "found", id: "1", wantStatus: http.StatusOK},
		{name: "not found", id: "2", svcErr: apperror.ErrNotFound, wantStatus: http.StatusNotFound},
		{name: "service fails", id: "1", svcErr: errors.New("db down"), wantStatus: http.StatusInternalServerError},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			h := NewUserHandler(&fakeUserService{err: tt.svcErr})
			r := chi.NewRouter()
			r.Get("/users/{id}", h.Get)

			req := httptest.NewRequest(http.MethodGet, "/users/"+tt.id, nil)
			w := httptest.NewRecorder()
			r.ServeHTTP(w, req)

			require.Equal(t, tt.wantStatus, w.Code)
			assert.NotContains(t, w.Body.String(), "db down") // no internal error text
		})
	}
}
```

   Middleware is a plain `func(http.Handler) http.Handler`: wrap a stub
   (`mw(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) }))`)
   and call `ServeHTTP` on it directly. For auth, sign test tokens with the same
   `auth.Verifier` key (`.claude/patterns/auth.md`).
   Calling a handler directly (no router) needs the route context set by hand:

```go
rctx := chi.NewRouteContext()
rctx.URLParams.Add("id", "1")
req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
```

4. **Run** `go test -race ./internal/handler/...`, then the quality gates.

## Rules

- Prefer serving through the router; it covers params and middleware order
- Assert status and the error body, not internal error strings
- Database-backed tests use testcontainers-go (`testing.md`)
