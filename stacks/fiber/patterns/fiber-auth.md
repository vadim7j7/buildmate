# Fiber: Auth and Rate-Limit Middleware

Fiber v3 wiring for the shared JWT pieces in `auth.md` (`Verifier`, `BearerToken`).
Rate limiting uses Fiber's own `limiter` middleware rather than the store in
`rate-limiting.md` (read that file for key and limit choices).

---

## 1. Authentication Middleware

```go
package middleware

import (
	"log/slog"

	"github.com/gofiber/fiber/v3"

	"example.com/app/internal/auth"
)

type claimsLocal struct{} // unexported key: no collisions with other Locals

// RequireAuth rejects requests without a valid bearer token.
func RequireAuth(v *auth.Verifier) fiber.Handler {
	return func(c fiber.Ctx) error {
		raw, ok := auth.BearerToken(c.Get(fiber.HeaderAuthorization))
		if !ok {
			return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{"error": "unauthorized", "code": "UNAUTHORIZED"})
		}
		claims, err := v.Verify(raw)
		if err != nil {
			slog.DebugContext(c, "token rejected", "err", err)
			return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{"error": "unauthorized", "code": "UNAUTHORIZED"})
		}
		fiber.Locals[*auth.Claims](c, claimsLocal{}, claims)
		return c.Next()
	}
}

// Claims returns the verified claims set by RequireAuth.
func Claims(c fiber.Ctx) (*auth.Claims, bool) {
	claims := fiber.Locals[*auth.Claims](c, claimsLocal{})
	return claims, claims != nil
}

// RequireRole must run after RequireAuth.
func RequireRole(roles ...string) fiber.Handler {
	return func(c fiber.Ctx) error {
		claims, ok := Claims(c)
		if !ok {
			return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{"error": "unauthorized", "code": "UNAUTHORIZED"})
		}
		for _, r := range roles {
			if claims.Role == r {
				return c.Next()
			}
		}
		return c.Status(fiber.StatusForbidden).JSON(fiber.Map{"error": "forbidden", "code": "FORBIDDEN"})
	}
}
```

In handlers, read the user with `middleware.Claims(c)` and pass `claims.Subject` to the
service as an explicit argument (`svc.ListOrders(c, userID)`): easy to test, and it does
not depend on how Fiber maps Locals to `context.Context`.

---

## 2. Rate Limiting (`middleware/limiter`)

```go
import "github.com/gofiber/fiber/v3/middleware/limiter"

func tooMany(c fiber.Ctx) error {
	return c.Status(fiber.StatusTooManyRequests).JSON(fiber.Map{"error": "too many requests", "code": "RATE_LIMITED"})
}

loginLimit := limiter.New(limiter.Config{
	Max:          5,
	Expiration:   time.Minute,
	KeyGenerator: func(c fiber.Ctx) string { return c.IP() },
	LimitReached: tooMany,
})

apiLimit := limiter.New(limiter.Config{
	Max:        120,
	Expiration: time.Minute,
	KeyGenerator: func(c fiber.Ctx) string {
		if claims, ok := middleware.Claims(c); ok {
			return "user:" + claims.Subject
		}
		return "ip:" + c.IP()
	},
	LimitReached: tooMany,
})
```

The limiter sets `Retry-After` and `X-RateLimit-*` headers itself. It keeps counters in
memory per process; with several instances pass a shared `Storage` (e.g. the Redis
storage from `github.com/gofiber/storage`).

`c.IP()` is the socket address unless proxy headers are trusted. Behind a load balancer
set `TrustProxy: true`, `TrustProxyConfig: fiber.TrustProxyConfig{Proxies: []string{...}}`
and `ProxyHeader: fiber.HeaderXForwardedFor` in `fiber.Config`; never trust the header
from everyone.

---

## 3. Wiring

```go
api := app.Group("/api/v1")
api.Post("/auth/login", loginLimit, h.Auth.Login) // runs left to right: limiter, then handler

authed := api.Group("", middleware.RequireAuth(verifier), apiLimit)
authed.Get("/users/me", h.User.Me)

admin := authed.Group("/admin", middleware.RequireRole("admin"))
admin.Get("/users", h.Admin.ListUsers)
```

---

## Rules

- Auth on groups; `/health` and public routes stay outside them
- Fixed JSON bodies for 401/403/429; never the token or the JWT error text
- Never keep `c` or values read from it after the handler returns (see zero-copy rules)
- Test with `app.Test` (the `/new-test` skill): missing, invalid and expired token, wrong
  role, limit exceeded
