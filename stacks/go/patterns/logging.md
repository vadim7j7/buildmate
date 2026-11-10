# Logging with slog and Request IDs

Structured logging with the standard library `log/slog`. Every log line written while
handling a request carries that request's ID, so one request can be followed across
handler, service and repository logs.

---

## 1. Logger Setup (once, in `main`)

```go
package main

import (
	"log/slog"
	"os"

	"example.com/app/internal/logging"
)

func newLogger(env string) *slog.Logger {
	opts := &slog.HandlerOptions{Level: slog.LevelInfo}
	var h slog.Handler
	if env == "development" {
		opts.Level = slog.LevelDebug
		h = slog.NewTextHandler(os.Stdout, opts)
	} else {
		h = slog.NewJSONHandler(os.Stdout, opts) // one JSON object per line
	}
	return slog.New(logging.ContextHandler{Handler: h})
}

// in main(): slog.SetDefault(newLogger(cfg.Environment))
```

---

## 2. Request ID in the Context

```go
package logging

import (
	"context"
	"crypto/rand"
	"log/slog"
	"net/http"
)

type requestIDKey struct{}

// WithRequestID returns a context carrying id.
func WithRequestID(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, requestIDKey{}, id)
}

// RequestID returns the request ID stored in ctx, if any.
func RequestID(ctx context.Context) (string, bool) {
	id, ok := ctx.Value(requestIDKey{}).(string)
	return id, ok
}

// ContextHandler adds request_id from the context to every record.
type ContextHandler struct{ slog.Handler }

func (h ContextHandler) Handle(ctx context.Context, r slog.Record) error {
	if id, ok := RequestID(ctx); ok {
		r.AddAttrs(slog.String("request_id", id))
	}
	return h.Handler.Handle(ctx, r)
}

func (h ContextHandler) WithAttrs(attrs []slog.Attr) slog.Handler {
	return ContextHandler{h.Handler.WithAttrs(attrs)}
}

func (h ContextHandler) WithGroup(name string) slog.Handler {
	return ContextHandler{h.Handler.WithGroup(name)}
}

// Middleware reuses a sane incoming X-Request-ID or makes one, and echoes it back.
func Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id := r.Header.Get("X-Request-ID")
		if !validID(id) {
			id = rand.Text() // Go 1.24+: 26 random base32 chars
		}
		w.Header().Set("X-Request-ID", id)
		next.ServeHTTP(w, r.WithContext(WithRequestID(r.Context(), id)))
	})
}

// validID rejects client IDs that could inject into logs or bloat them.
func validID(id string) bool {
	if id == "" || len(id) > 64 {
		return false
	}
	for _, c := range id {
		if !(c == '-' || c == '_' || c >= '0' && c <= '9' || c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z') {
			return false
		}
	}
	return true
}
```

### Framework wiring

- **net/http / Chi**: `r.Use(logging.Middleware)`. If the project already uses
  `chimw.RequestID`, read it with `chimw.GetReqID(ctx)` in `ContextHandler` instead of
  adding a second ID.
- **Gin**: wrap the same logic in a `gin.HandlerFunc` and pass the new context on with
  `c.Request = c.Request.WithContext(logging.WithRequestID(c.Request.Context(), id))`;
  log with `c.Request.Context()`.
- **Fiber**: use `github.com/gofiber/fiber/v3/middleware/requestid` and add
  `"request_id", requestid.FromContext(c)` to log calls (or a per-request
  `slog.With(...)` logger); check the middleware docs for the exact helper in your version.

---

## 3. Writing Log Lines

```go
slog.InfoContext(ctx, "user created", "user_id", user.ID)
slog.ErrorContext(ctx, "charge failed", "order_id", order.ID, "err", err)

// Request log (one line per request), in the request-logger middleware:
slog.InfoContext(r.Context(), "request",
	"method", r.Method, "path", r.URL.Path,
	"status", status, "duration_ms", time.Since(start).Milliseconds())
```

---

## Rules

- Always the `*Context` variants (`InfoContext`, `ErrorContext`) so `request_id` is attached
- Key-value pairs with stable snake_case keys (`user_id`, `err`, `duration_ms`); no
  `fmt.Sprintf` into the message
- Log an error once, where it is handled (usually the handler or `handleError`), not at
  every layer that wraps it
- Never log secrets, tokens, passwords, full request bodies or `Authorization` headers;
  log IDs, not personal data
- Debug level for noise; production runs at Info
- One logger configured in `main`; libraries take a `*slog.Logger` or use `slog.Default()`,
  never their own `log.Printf`
