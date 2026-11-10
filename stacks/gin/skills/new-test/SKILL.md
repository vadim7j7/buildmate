---
name: new-test
description: Write table-driven httptest tests for a Gin handler or middleware
---

# /new-test

## What This Does

Writes tests for an existing Gin handler, middleware or service: table-driven cases
that drive a real `gin.Engine` through `httptest`, with a fake service behind it.

## Usage

```
/new-test internal/handler/user.go          # handler tests
/new-test internal/middleware/auth.go       # middleware tests
/new-test UserService.CreateUser            # service unit test
```

## How It Works

1. **Read** `.claude/patterns/testing.md`, `.claude/patterns/gin-patterns.md` and the
   code under test. Look at existing `*_test.go` files and reuse their fakes and helpers.
2. **List the cases** before writing: success, each validation failure, not found,
   unauthorized/forbidden (if the route is protected), service error -> 500 with the
   fixed message.
3. **Write the test** next to the file (`user_test.go`):

```go
func TestUserHandler_Create(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name       string
		body       string
		svcErr     error
		wantStatus int
		wantCode   string
	}{
		{name: "created", body: `{"name":"Ann","email":"ann@example.com"}`, wantStatus: http.StatusCreated},
		{name: "invalid email", body: `{"name":"Ann","email":"nope"}`, wantStatus: http.StatusBadRequest, wantCode: "VALIDATION_FAILED"},
		{name: "malformed json", body: `{`, wantStatus: http.StatusBadRequest, wantCode: "INVALID_BODY"},
		{name: "service fails", body: `{"name":"Ann","email":"ann@example.com"}`, svcErr: errors.New("db down"), wantStatus: http.StatusInternalServerError, wantCode: "INTERNAL"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			h := NewUserHandler(&fakeUserService{err: tt.svcErr})
			r := gin.New()
			r.POST("/users", h.Create)

			req := httptest.NewRequest(http.MethodPost, "/users", strings.NewReader(tt.body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()
			r.ServeHTTP(w, req)

			require.Equal(t, tt.wantStatus, w.Code)
			if tt.wantCode != "" {
				var got struct{ Code string `json:"code"` }
				require.NoError(t, json.Unmarshal(w.Body.Bytes(), &got))
				assert.Equal(t, tt.wantCode, got.Code)
			}
			assert.NotContains(t, w.Body.String(), "db down") // no internal error text
		})
	}
}
```

   Middleware: register it plus a stub handler (`r.GET("/x", mw, func(c *gin.Context) { c.Status(http.StatusOK) })`)
   and assert both the blocked and the passing request. For auth, sign test tokens with
   the same `auth.Verifier` key (`.claude/patterns/auth.md`).
4. **Run** `go test -race ./internal/handler/...`, then the quality gates
   (`gofmt -w`, `golangci-lint run ./...`, `go test ./...`).

## Rules

- Test through the router (`r.ServeHTTP`), not by calling the handler with a hand-made
  `gin.Context`: path params and middleware must be exercised
- Assert status and error `code`, not full error strings
- Database-backed tests use testcontainers-go (`testing.md`), never a shared dev database
