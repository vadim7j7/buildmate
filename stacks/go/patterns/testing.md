# Go Testing

Table-driven unit tests, HTTP handler tests with `httptest`, and integration tests
against a real database in a container (testcontainers-go). Extends the short testing
section in `backend-patterns.md`.

```bash
go test ./...                       # all
go test -race ./...                 # always before finishing: catches data races
go test -run 'TestUserService/not_found' ./internal/service/
go test -short ./...                # skips integration tests (see section 4)
```

---

## 1. Table-Driven Tests

```go
func TestSlugify(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name string
		in   string
		want string
	}{
		{name: "lowercases", in: "Hello", want: "hello"},
		{name: "spaces to dashes", in: "a b c", want: "a-b-c"},
		{name: "empty", in: "", want: ""},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel() // safe: tt is per-iteration since Go 1.22
			assert.Equal(t, tt.want, Slugify(tt.in))
		})
	}
}
```

- `require` stops the test (use for setup and preconditions), `assert` keeps going
- Compare errors with `require.ErrorIs(t, err, ErrNotFound)`, never by message
- Name cases by behaviour (`"not found"`, `"duplicate email"`), so `-run` can select them

---

## 2. Fakes Over Mock Frameworks

Services depend on small interfaces, so a hand-written fake is usually enough:

```go
type fakeUserRepo struct {
	users map[string]*User
	err   error // forced error, if set
}

func (f *fakeUserRepo) FindByID(_ context.Context, id string) (*User, error) {
	if f.err != nil {
		return nil, f.err
	}
	u, ok := f.users[id]
	if !ok {
		return nil, ErrNotFound
	}
	return u, nil
}
```

Use `testify/mock` or gomock only if the project already does.

---

## 3. HTTP Handler Tests (httptest)

Drive the real router, so routing, middleware and param parsing are covered.

```go
func TestGetUser(t *testing.T) {
	repo := &fakeUserRepo{users: map[string]*User{"1": {ID: "1", Name: "Alice"}}}
	srv := NewRouter(NewUserHandler(NewUserService(repo))) // http.Handler

	tests := []struct {
		name       string
		path       string
		wantStatus int
		wantBody   string
	}{
		{"found", "/api/v1/users/1", http.StatusOK, `"name":"Alice"`},
		{"not found", "/api/v1/users/2", http.StatusNotFound, `"error":"resource not found"`},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodGet, tt.path, nil)
			rec := httptest.NewRecorder()

			srv.ServeHTTP(rec, req)

			require.Equal(t, tt.wantStatus, rec.Code)
			assert.Contains(t, rec.Body.String(), tt.wantBody)
		})
	}
}
```

For JSON bodies: `httptest.NewRequest(http.MethodPost, "/users", strings.NewReader(body))`
plus `req.Header.Set("Content-Type", "application/json")`. Decode the response with
`json.Unmarshal(rec.Body.Bytes(), &got)` when you assert on fields.
For a full server (cookies, redirects, real client): `ts := httptest.NewServer(srv)`,
`defer ts.Close()`, `http.Get(ts.URL + "/health")`.

---

## 4. Integration Tests with testcontainers-go

Needs Docker. Start one container per package in `TestMain`, run migrations, and isolate
tests by truncating tables or by running each test in a rolled-back transaction.

```go
package repository_test

import (
	"context"
	"flag"
	"log"
	"os"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/modules/postgres"
)

var pool *pgxpool.Pool

func TestMain(m *testing.M) {
	flag.Parse()
	if testing.Short() {
		os.Exit(0) // go test -short skips containers
	}
	os.Exit(run(m))
}

func run(m *testing.M) int {
	ctx := context.Background()
	ctr, err := postgres.Run(ctx, "postgres:17-alpine",
		postgres.WithDatabase("app_test"),
		postgres.WithUsername("app"),
		postgres.WithPassword("secret"),
		postgres.BasicWaitStrategies(),
	)
	if err != nil {
		log.Printf("start postgres: %v", err)
		return 1
	}
	defer func() { _ = testcontainers.TerminateContainer(ctr) }()

	dsn, err := ctr.ConnectionString(ctx, "sslmode=disable")
	if err != nil {
		log.Printf("dsn: %v", err)
		return 1
	}
	pool, err = pgxpool.New(ctx, dsn)
	if err != nil {
		log.Printf("connect: %v", err)
		return 1
	}
	defer pool.Close()
	// apply migrations here (goose, see the /new-migration skill)
	return m.Run()
}
```

Other databases have modules with the same shape: `modules/mysql` (`mysql.Run(ctx, "mysql:8.4", ...)`),
`modules/mongodb` (`mongodb.Run(ctx, "mongo:8")`). SQLite needs no container: open a file in
`t.TempDir()`. Check the module docs for option names before using an unfamiliar one.

---

## Rules

- Test files sit next to the code (`user.go` / `user_test.go`); black-box tests use the
  `package foo_test` name
- `t.Parallel()` only when the test shares no mutable state (DB rows, globals, env)
- `t.Context()` (Go 1.24+) for contexts that end with the test; `t.Cleanup` for teardown;
  `t.Setenv` instead of `os.Setenv`
- No `time.Sleep` to wait for goroutines: use channels, `sync.WaitGroup` or
  `require.Eventually`
- Every bug fix gets a test that failed before the fix
- Run `go test -race ./...` before reporting done
