# Gin: Auth and Rate-Limit Middleware

Gin wiring for the shared pieces in `auth.md` (JWT `Verifier`, `ClaimsFrom`) and
`rate-limiting.md` (per-key `ratelimit.Store`).

---

## 1. Authentication Middleware

```go
package middleware

import (
	"log/slog"
	"net/http"

	"github.com/gin-gonic/gin"

	"example.com/app/internal/auth"
)

// RequireAuth rejects requests without a valid bearer token and stores the claims
// in the request context, where services can read them with auth.ClaimsFrom.
func RequireAuth(v *auth.Verifier) gin.HandlerFunc {
	return func(c *gin.Context) {
		raw, ok := auth.BearerToken(c.GetHeader("Authorization"))
		if !ok {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized", "code": "UNAUTHORIZED"})
			return
		}
		claims, err := v.Verify(raw)
		if err != nil {
			slog.DebugContext(c.Request.Context(), "token rejected", "err", err)
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized", "code": "UNAUTHORIZED"})
			return
		}
		c.Request = c.Request.WithContext(auth.WithClaims(c.Request.Context(), claims))
		c.Next()
	}
}

// RequireRole must run after RequireAuth.
func RequireRole(roles ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		claims, ok := auth.ClaimsFrom(c.Request.Context())
		if !ok {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized", "code": "UNAUTHORIZED"})
			return
		}
		for _, r := range roles {
			if claims.Role == r {
				c.Next()
				return
			}
		}
		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "forbidden", "code": "FORBIDDEN"})
	}
}
```

Store claims in `c.Request.Context()` (not only `c.Set`): handlers pass
`c.Request.Context()` to services, so the user travels with it.

---

## 2. Rate-Limit Middleware

```go
// RateLimit allows each key its own token bucket; key picks the client.
func RateLimit(store *ratelimit.Store, key func(*gin.Context) string) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !store.Allow(key(c)) {
			c.Header("Retry-After", "1")
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{"error": "too many requests", "code": "RATE_LIMITED"})
			return
		}
		c.Next()
	}
}

func ByIP(c *gin.Context) string { return c.ClientIP() }

func ByUser(c *gin.Context) string {
	if claims, ok := auth.ClaimsFrom(c.Request.Context()); ok {
		return "user:" + claims.Subject
	}
	return "ip:" + c.ClientIP()
}
```

`c.ClientIP()` trusts `X-Forwarded-For` from any proxy by default. Set the proxies you
actually run behind, once at startup:

```go
if err := r.SetTrustedProxies([]string{"10.0.0.0/8"}); err != nil { // or nil: trust none
	return fmt.Errorf("trusted proxies: %w", err)
}
```

---

## 3. Wiring

```go
// ctx lives as long as the server; cancelling it stops the limiters' eviction goroutines.
loginLimit := ratelimit.NewStore(ctx, rate.Every(12*time.Second), 5)
apiLimit := ratelimit.NewStore(ctx, rate.Every(time.Second), 20)

api := r.Group("/api/v1")
api.POST("/auth/login", middleware.RateLimit(loginLimit, middleware.ByIP), h.Auth.Login)

authed := api.Group("")
authed.Use(middleware.RequireAuth(verifier), middleware.RateLimit(apiLimit, middleware.ByUser))
{
	authed.GET("/users/me", h.User.Me)

	admin := authed.Group("/admin", middleware.RequireRole("admin"))
	admin.GET("/users", h.Admin.ListUsers)
}
```

---

## Rules

- Auth middleware on groups, never checked inside each handler
- Abort with a fixed JSON body; never return the token or the JWT error text
- `/health` and public routes stay outside the authenticated group
- Rate-limit login, sign-up and password reset by IP (and email), the API by user
- Test middleware with `httptest` (see the `/new-test` skill): missing token, bad token,
  expired token, wrong role, limit exceeded
