# Go Code Patterns

Reference patterns for Go development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Interface-Based Design

Define behavior with interfaces, implement with structs.

```go
// UserService defines operations on users.
type UserService interface {
	GetUser(ctx context.Context, id string) (*User, error)
	CreateUser(ctx context.Context, input CreateUserInput) (*User, error)
	ListUsers(ctx context.Context, filter UserFilter) ([]User, error)
}

type userService struct {
	repo   UserRepository
	logger *slog.Logger
}

// NewUserService creates a new UserService.
func NewUserService(repo UserRepository, logger *slog.Logger) UserService {
	return &userService{repo: repo, logger: logger}
}
```

### Interface Rules

- Keep interfaces small (1-3 methods)
- Define interfaces where they are used, not where they are implemented
- Accept interfaces, return structs
- Name single-method interfaces with `-er` suffix: `Reader`, `Writer`, `Closer`

---

## 2. Error Handling

Wrap errors with context at each layer.

```go
func (s *userService) GetUser(ctx context.Context, id string) (*User, error) {
	if id == "" {
		return nil, fmt.Errorf("get user: %w", ErrValidation)
	}

	user, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("get user %s: %w", id, err)
	}

	return user, nil
}
```

### Error Rules

- Always wrap errors with `fmt.Errorf("context: %w", err)`
- Use sentinel errors for expected conditions (`ErrNotFound`, `ErrValidation`)
- Check errors immediately after the call
- Never ignore errors (use `_ =` only with comment explaining why)
- Return errors, never panic in library code

---

## 3. Repository Pattern

Encapsulate database access behind an interface.

```go
// UserRepository defines data access for users.
type UserRepository interface {
	FindAll(ctx context.Context) ([]User, error)
	FindByID(ctx context.Context, id string) (*User, error)
	Create(ctx context.Context, user *User) error
	Update(ctx context.Context, user *User) error
	Delete(ctx context.Context, id string) error
}

type pgUserRepo struct {
	db *sql.DB
}

func NewUserRepository(db *sql.DB) UserRepository {
	return &pgUserRepo{db: db}
}

func (r *pgUserRepo) FindByID(ctx context.Context, id string) (*User, error) {
	var u User
	err := r.db.QueryRowContext(ctx,
		"SELECT id, name, email, created_at FROM users WHERE id = $1", id,
	).Scan(&u.ID, &u.Name, &u.Email, &u.CreatedAt)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, fmt.Errorf("find user %s: %w", id, ErrNotFound)
	}
	if err != nil {
		return nil, fmt.Errorf("find user %s: %w", id, err)
	}
	return &u, nil
}
```

### Repository Rules

- One repository per aggregate/entity
- Use parameterized queries (never string concatenation)
- Return domain types, not database types
- Wrap `sql.ErrNoRows` with domain-specific `ErrNotFound`
- Always pass `context.Context` for cancellation

---

## 4. Service Layer

Business logic lives in services, not handlers.

```go
type orderService struct {
	orderRepo OrderRepository
	userRepo  UserRepository
	notifier  Notifier
}

func (s *orderService) PlaceOrder(ctx context.Context, input PlaceOrderInput) (*Order, error) {
	user, err := s.userRepo.FindByID(ctx, input.UserID)
	if err != nil {
		return nil, fmt.Errorf("place order: find user: %w", err)
	}

	order := &Order{
		UserID: user.ID,
		Items:  input.Items,
		Status: OrderStatusPending,
	}

	if err := s.orderRepo.Create(ctx, order); err != nil {
		return nil, fmt.Errorf("place order: create: %w", err)
	}

	if err := s.notifier.Notify(ctx, user.Email, "Order placed"); err != nil {
		s.logger.Error("failed to notify", "err", err, "order_id", order.ID)
		// Non-critical, don't fail the order
	}

	return order, nil
}
```

---

## 5. Configuration Pattern

Load configuration from environment with sensible defaults.

```go
package config

import (
	"os"
	"strconv"
	"time"
)

type Config struct {
	DatabaseURL    string
	Port           string
	Environment    string
	ReadTimeout    time.Duration
	WriteTimeout   time.Duration
	MaxConnections int
}

func Load() *Config {
	return &Config{
		DatabaseURL:    getEnv("DATABASE_URL", "postgres://localhost/myapp_dev"),
		Port:           getEnv("PORT", "8080"),
		Environment:    getEnv("APP_ENV", "development"),
		ReadTimeout:    getDuration("READ_TIMEOUT", 5*time.Second),
		WriteTimeout:   getDuration("WRITE_TIMEOUT", 10*time.Second),
		MaxConnections: getInt("MAX_CONNECTIONS", 25),
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getInt(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return fallback
}

func getDuration(key string, fallback time.Duration) time.Duration {
	if v := os.Getenv(key); v != "" {
		if d, err := time.ParseDuration(v); err == nil {
			return d
		}
	}
	return fallback
}
```

---

## 6. Testing Patterns

### Table-Driven Test

```go
func TestUserService_GetUser(t *testing.T) {
	tests := []struct {
		name    string
		id      string
		setup   func(*mockUserRepo)
		want    *User
		wantErr error
	}{
		{
			name:  "existing user",
			id:    "1",
			setup: func(m *mockUserRepo) { m.users = []User{{ID: "1", Name: "Alice"}} },
			want:  &User{ID: "1", Name: "Alice"},
		},
		{
			name:    "not found",
			id:      "999",
			setup:   func(m *mockUserRepo) {},
			wantErr: ErrNotFound,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			repo := &mockUserRepo{}
			tt.setup(repo)
			svc := NewUserService(repo, slog.Default())

			got, err := svc.GetUser(context.Background(), tt.id)
			if tt.wantErr != nil {
				require.ErrorIs(t, err, tt.wantErr)
				return
			}
			require.NoError(t, err)
			assert.Equal(t, tt.want.ID, got.ID)
		})
	}
}
```

### HTTP Handler Test

```go
func TestUserHandler_List(t *testing.T) {
	svc := &mockUserService{
		users: []User{{ID: "1", Name: "Alice"}},
	}
	handler := NewUserHandler(svc)

	req := httptest.NewRequest(http.MethodGet, "/users", nil)
	w := httptest.NewRecorder()

	handler.List(w, req)

	require.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "Alice")
}
```

### Test Rules

- Use table-driven tests with `t.Run` for subtests
- Use `_test` package for black-box testing
- Use `testify/require` for fatal checks, `testify/assert` for non-fatal
- Name test functions `TestTypeName_MethodName`
- Use `httptest` for handler tests
- Use `t.Helper()` in test helper functions
