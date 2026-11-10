# Chi: Auth and Rate-Limit Middleware

Chi middleware is plain `func(http.Handler) http.Handler`, so the shared pieces in
`auth.md` (`Verifier`, `BearerToken`, `WithClaims` / `ClaimsFrom`) plug in directly.
Rate limiting uses `github.com/go-chi/httprate` (read `rate-limiting.md` for key and
limit choices).

---

## 1. Authentication Middleware

```go
package middleware

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"example.com/app/internal/auth"
)

// RequireAuth rejects requests without a valid bearer token and puts the claims
// in the request context (read them with auth.ClaimsFrom).
func RequireAuth(v *auth.Verifier) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			raw, ok := auth.BearerToken(r.Header.Get("Authorization"))
			if !ok {
				writeError(w, http.StatusUnauthorized, "unauthorized")
				return
			}
			claims, err := v.Verify(raw)
			if err != nil {
				slog.DebugContext(r.Context(), "token rejected", "err", err)
				writeError(w, http.StatusUnauthorized, "unauthorized")
				return
			}
			next.ServeHTTP(w, r.WithContext(auth.WithClaims(r.Context(), claims)))
		})
	}
}

// RequireRole must run after RequireAuth.
func RequireRole(roles ...string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			claims, ok := auth.ClaimsFrom(r.Context())
			if !ok {
				writeError(w, http.StatusUnauthorized, "unauthorized")
				return
			}
			for _, role := range roles {
				if claims.Role == role {
					next.ServeHTTP(w, r)
					return
				}
			}
			writeError(w, http.StatusForbidden, "forbidden")
		})
	}
}

func writeError(w http.ResponseWriter, status int, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{"error": msg})
}
```

Reuse the project's `respondError` instead of `writeError` if the middleware package
can import it.

---

## 2. Rate Limiting (`github.com/go-chi/httprate`)

```go
import "github.com/go-chi/httprate"

// Per IP: 5 login attempts per minute.
loginLimit := httprate.LimitByIP(5, time.Minute)

// Per user after auth, falling back to IP.
apiLimit := httprate.Limit(120, time.Minute,
	httprate.WithKeyFuncs(func(r *http.Request) (string, error) {
		if claims, ok := auth.ClaimsFrom(r.Context()); ok {
			return "user:" + claims.Subject, nil
		}
		return httprate.KeyByIP(r)
	}),
	httprate.WithLimitHandler(func(w http.ResponseWriter, r *http.Request) {
		writeError(w, http.StatusTooManyRequests, "too many requests")
	}),
)
```

httprate counts in memory per process; for several instances use its Redis backend
(`github.com/go-chi/httprate-redis`). `KeyByIP` uses `r.RemoteAddr`; it is the real
client only if `chimw.RealIP` runs first, and `RealIP` trusts the headers from anyone,
so use it only behind a proxy that overwrites `X-Forwarded-For` / `X-Real-IP`.

---

## 3. Wiring

```go
r.Route("/api/v1", func(r chi.Router) {
	r.With(loginLimit).Post("/auth/login", h.Auth.Login)

	r.Group(func(r chi.Router) {
		r.Use(middleware.RequireAuth(verifier), apiLimit)
		r.Get("/users/me", h.User.Me)

		r.With(middleware.RequireRole("admin")).Get("/admin/users", h.Admin.ListUsers)
	})
})
```

---

## Rules

- Auth in `r.Group` / `r.With`; `/health` and public routes stay outside
- Fixed JSON bodies for 401/403/429; never the token or the JWT error text
- Context keys are unexported types (`auth.ClaimsFrom`), never strings
- Test with `httptest` through the router (the `/new-test` skill): missing, invalid and
  expired token, wrong role, limit exceeded
