# Authentication (framework-neutral parts)

Token verification, the claims-in-context helpers and password hashing, shared by every
Go web framework. The middleware that wires this into the router is in the framework
pattern (`gin-auth.md`, `fiber-auth.md`, `chi-auth.md`).

Pick one scheme per API and keep it:

- **JWT bearer tokens** (shown here): stateless APIs, mobile clients, other services.
  Short-lived access tokens (5-15 min) plus a refresh token stored server-side, so
  logout and revocation work
- **Server-side sessions** (e.g. `github.com/alexedwards/scs/v2`): browser apps on the
  same site; an `HttpOnly` cookie holds only the session ID. Needs CSRF protection

If a hosted identity provider (Auth0, Cognito, Keycloak...) issues the tokens, verify
them against its JWKS (RS256/ES256) instead of a shared secret; the middleware shape
is the same.

---

## 1. Verifying JWTs (`github.com/golang-jwt/jwt/v5`)

```go
package auth

import (
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

var ErrUnauthenticated = errors.New("unauthenticated")

// Claims are the token claims this API relies on.
type Claims struct {
	Role string `json:"role"`
	jwt.RegisteredClaims // Subject holds the user ID
}

// Verifier checks HS256 tokens issued by this service.
type Verifier struct {
	key      []byte
	issuer   string
	audience string
}

func NewVerifier(key []byte, issuer, audience string) (*Verifier, error) {
	if len(key) < 32 {
		return nil, errors.New("auth: signing key must be at least 32 bytes")
	}
	return &Verifier{key: key, issuer: issuer, audience: audience}, nil
}

// Verify parses raw and returns its claims, or ErrUnauthenticated.
func (v *Verifier) Verify(raw string) (*Claims, error) {
	claims := &Claims{}
	_, err := jwt.ParseWithClaims(raw, claims,
		func(*jwt.Token) (any, error) { return v.key, nil },
		jwt.WithValidMethods([]string{"HS256"}), // blocks alg=none and alg confusion
		jwt.WithIssuer(v.issuer),
		jwt.WithAudience(v.audience),
		jwt.WithExpirationRequired(),
		jwt.WithLeeway(30*time.Second),
	)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrUnauthenticated, err) // log the cause, never send it
	}
	if claims.Subject == "" {
		return nil, fmt.Errorf("%w: no subject", ErrUnauthenticated)
	}
	return claims, nil
}

// BearerToken extracts the token from an Authorization header value.
func BearerToken(header string) (string, bool) {
	scheme, token, ok := strings.Cut(header, " ")
	if !ok || !strings.EqualFold(scheme, "Bearer") || token == "" {
		return "", false
	}
	return token, true
}
```

Issuing (login handler, after the password check):

```go
now := time.Now()
claims := auth.Claims{
	Role: user.Role,
	RegisteredClaims: jwt.RegisteredClaims{
		Subject:   user.ID,
		Issuer:    issuer,
		Audience:  jwt.ClaimStrings{audience},
		IssuedAt:  jwt.NewNumericDate(now),
		ExpiresAt: jwt.NewNumericDate(now.Add(15 * time.Minute)),
	},
}
signed, err := jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString(key)
```

---

## 2. Claims in the Context

Middleware stores the verified claims; services read the user from `context.Context`
(or take the user ID as an explicit argument, which is easier to test).

```go
type claimsKey struct{}

func WithClaims(ctx context.Context, c *Claims) context.Context {
	return context.WithValue(ctx, claimsKey{}, c)
}

func ClaimsFrom(ctx context.Context) (*Claims, bool) {
	c, ok := ctx.Value(claimsKey{}).(*Claims)
	return c, ok && c != nil
}
```

---

## 3. Passwords (`golang.org/x/crypto/bcrypt`)

```go
func HashPassword(pw string) (string, error) {
	h, err := bcrypt.GenerateFromPassword([]byte(pw), bcrypt.DefaultCost)
	if err != nil {
		return "", fmt.Errorf("hash password: %w", err) // ErrPasswordTooLong over 72 bytes
	}
	return string(h), nil
}

func CheckPassword(hash, pw string) bool {
	return bcrypt.CompareHashAndPassword([]byte(hash), []byte(pw)) == nil
}
```

Validate passwords as `min=8,max=72` so bcrypt never truncates or rejects them. argon2id
(`golang.org/x/crypto/argon2`) is fine too; do not mix schemes without a migration plan.

---

## Rules

- Login failure says "invalid email or password" for both unknown email and wrong password
- 401 for a missing/invalid token, 403 for a valid user without the permission; the body
  is a fixed message, never the jwt error text
- Signing key from the environment, at least 32 random bytes, required at startup
- Always pin the algorithm (`WithValidMethods`) and check `exp`, `iss`, `aud`
- Tokens never in URLs or logs; rate-limit login and password reset (`rate-limiting.md`)
