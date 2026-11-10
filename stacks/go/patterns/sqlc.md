# sqlc: Type-Safe SQL

**SQL databases only (PostgreSQL, MySQL, SQLite).** MongoDB projects: ignore this file.

sqlc generates Go code from plain SQL queries and your migration files. It is an
alternative to hand-written repository queries; use it only if the project already
has `sqlc.yaml`, or when asked to introduce it. Never mix generated and hand-written
queries for the same table.

---

## 1. Setup

```bash
go get -tool github.com/sqlc-dev/sqlc/cmd/sqlc   # Go 1.24+: pinned in go.mod
go tool sqlc generate                            # after every query or migration change
go tool sqlc vet                                 # optional: lint queries
```

`sqlc.yaml` (PostgreSQL + pgx v5 shown; for MySQL use `engine: "mysql"`, for SQLite
`engine: "sqlite"`, and drop `sql_package`, which makes sqlc emit `database/sql` code):

```yaml
version: "2"
sql:
  - engine: "postgresql"
    schema: "db/migrations"     # goose migrations: sqlc ignores the -- +goose Down parts
    queries: "db/queries"
    gen:
      go:
        package: "db"
        out: "internal/db"
        sql_package: "pgx/v5"
        emit_json_tags: true
        emit_empty_slices: true  # List queries return [] not nil (JSON "[]")
```

---

## 2. Queries

One file per table in `db/queries/`. The comment names the method and its shape:
`:one` (single row, `pgx.ErrNoRows` / `sql.ErrNoRows` when none), `:many`, `:exec`,
`:execrows` (returns affected rows).

```sql
-- name: GetUser :one
SELECT id, name, email, created_at FROM users WHERE id = $1;

-- name: ListUsers :many
SELECT id, name, email, created_at FROM users
ORDER BY id
LIMIT $1 OFFSET $2;

-- name: CreateUser :one
INSERT INTO users (name, email) VALUES ($1, $2)
RETURNING id, name, email, created_at;

-- name: DeleteUser :execrows
DELETE FROM users WHERE id = $1;
```

Use `sqlc.arg(name)` / `sqlc.narg(name)` to name parameters when `$1` would be unclear
(MySQL/SQLite use `?`).

---

## 3. Repository Wrapping Generated Code

Generated code lives in `internal/db` and is never edited. A repository adapts it to the
domain type and maps "no rows" to `ErrNotFound`, so services do not import `internal/db`.

```go
package repository

import (
	"context"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"example.com/app/internal/db"
	"example.com/app/internal/domain"
)

type UserRepo struct {
	pool *pgxpool.Pool // for transactions
	q    *db.Queries
}

func NewUserRepo(pool *pgxpool.Pool) *UserRepo {
	return &UserRepo{pool: pool, q: db.New(pool)}
}

func (r *UserRepo) FindByID(ctx context.Context, id int64) (*domain.User, error) {
	row, err := r.q.GetUser(ctx, id)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, fmt.Errorf("find user %d: %w", id, domain.ErrNotFound)
	}
	if err != nil {
		return nil, fmt.Errorf("find user %d: %w", id, err)
	}
	return &domain.User{ID: row.ID, Name: row.Name, Email: row.Email}, nil
}
```

With `database/sql` (MySQL, SQLite) the same shape holds: `db.New(sqlDB)`, `sql.ErrNoRows`,
and `sqlDB.BeginTx(ctx, nil)` for transactions.

---

## 4. Transactions

```go
func (r *UserRepo) CreateWithProfile(ctx context.Context, in domain.NewUser) error {
	tx, err := r.pool.Begin(ctx)
	if err != nil {
		return fmt.Errorf("begin: %w", err)
	}
	defer func() { _ = tx.Rollback(ctx) }() // no-op after Commit

	q := r.q.WithTx(tx)
	user, err := q.CreateUser(ctx, db.CreateUserParams{Name: in.Name, Email: in.Email})
	if err != nil {
		return fmt.Errorf("create user: %w", err)
	}
	if err := q.CreateProfile(ctx, user.ID); err != nil {
		return fmt.Errorf("create profile: %w", err)
	}
	return tx.Commit(ctx)
}
```

---

## Rules

- Run `go tool sqlc generate` after changing a query or a migration, and commit the output
- Never edit files under the generated `out` directory
- `schema` points at the migrations folder, so the schema has one source of truth
- Map generated row structs to domain types in the repository; handlers never see them
- Dynamic filters that sqlc cannot express: a small hand-written query in the same
  repository, still parameterized
