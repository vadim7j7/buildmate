# Go Web Security

Input validation, authentication, secrets, HTTP hardening and dependency scanning.
Auth middleware details: `auth.md`. Rate limiting: `rate-limiting.md`.

---

## 1. Input Validation

Validate at the edge (handler), with struct tags and go-playground/validator
(Gin: `binding:"..."`, Fiber/Chi: `validate:"..."`).

```go
type CreateUserRequest struct {
	Name  string `json:"name" validate:"required,min=1,max=100"`
	Email string `json:"email" validate:"required,email,max=254"`
	Role  string `json:"role" validate:"omitempty,oneof=admin member"`
}
```

With plain `net/http` / Chi decode strictly and cap the body size:

```go
func decodeJSON(w http.ResponseWriter, r *http.Request, dst any) error {
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20) // 1 MiB
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	if err := dec.Decode(dst); err != nil {
		return fmt.Errorf("decode body: %w", err)
	}
	if dec.More() {
		return errors.New("decode body: trailing data")
	}
	return validate.Struct(dst) // one *validator.Validate, created at startup
}
```

- Every string has a `max`; every number a range; enums use `oneof`
- Bind only the fields a client may set: separate request structs, never decode into the
  DB model (mass assignment: `role`, `is_admin`, `owner_id`)
- Return validation failures as `fields: [{field, rule}]`, never the raw error string
- IDs from the path are parsed (`strconv.ParseInt`, `uuid.Parse`) and rejected if invalid

---

## 2. Authorization

- Authentication middleware on the route group; authorization (may this user touch
  this record?) in the service, by filtering on the owner:
  `WHERE id = $1 AND owner_id = $2`. Return `ErrNotFound`, not 403, for other users' records
- Default deny: new routes go in the authenticated group unless they are explicitly public
- Role checks read the role from verified claims or the database, never from the request body

---

## 3. Secrets and Configuration

- Secrets come from the environment (or a secret manager); never in code, tests, logs
  or error messages. `.env` files are git-ignored
- No default for a secret: fail at startup if `JWT_SECRET` / `DATABASE_URL` is missing in
  production, instead of falling back to a dev value

```go
func mustEnv(key string) string {
	v := os.Getenv(key)
	if v == "" {
		log.Fatalf("missing required env var %s", key) // name only, never the value
	}
	return v
}
```

- Compare secrets and tokens with `subtle.ConstantTimeCompare`, never `==`
- Random tokens from `crypto/rand` (`rand.Text()` in Go 1.24+), never `math/rand`

---

## 4. HTTP Hardening

```go
srv := &http.Server{
	Addr:              ":" + port,
	Handler:           handler,
	ReadHeaderTimeout: 5 * time.Second, // Slowloris; gosec G112 flags its absence
	ReadTimeout:       15 * time.Second,
	WriteTimeout:      30 * time.Second,
	IdleTimeout:       60 * time.Second,
	MaxHeaderBytes:    1 << 20,
}
```

- CORS: an explicit origin allowlist; never `*` together with credentials
- Cookies: `HttpOnly`, `Secure`, `SameSite=Lax` (or `Strict`); session cookies need CSRF
  protection for unsafe methods (`http.CrossOriginProtection` in Go 1.25+, or a token)
- Behind a proxy, trust `X-Forwarded-For` only from known proxies (Gin `SetTrustedProxies`,
  Fiber `TrustProxy` config); chi's `RealIP` trusts any client
- Errors to clients: fixed messages and codes; details go to logs (`logging.md`)

---

## 5. SQL and Other Injection

- Parameterized queries only (`$1` / `?`); never `fmt.Sprintf` user input into SQL.
  Dynamic `ORDER BY` columns come from an allowlist map
- MongoDB: build filters from typed values, never decode request JSON into `bson.M`
- `os/exec`: pass arguments as separate strings, never through `sh -c`
- File paths from input: `os.Root` (Go 1.24+) or `filepath.IsLocal` before joining
- Templates: `html/template`, not `text/template`, for HTML

---

## 6. Dependency Scanning

```bash
go run golang.org/x/vuln/cmd/govulncheck@latest ./...
```

govulncheck reports only vulnerabilities in code your program actually calls, and exits
non-zero when it finds any (it is a quality gate in this project). Fix by upgrading the
module (`go get example.com/mod@vX.Y.Z && go mod tidy`) or the Go toolchain when the finding
is in the standard library. `golangci-lint` with `gosec` enabled covers common code-level
issues (weak crypto, missing timeouts, unchecked paths).

---

## Rules

- Never trust the client: validate, cap sizes, check ownership in the service
- Secrets only from the environment, never logged, required at startup
- Server timeouts always set; no bare `http.ListenAndServe`
- govulncheck clean before reporting done
