# Go Style Guide

Mandatory style rules for all Go code in this project. These are enforced by gofmt,
golangci-lint, and code review.

---

## 1. Formatting

All code MUST be formatted with `gofmt`. No exceptions.

```bash
gofmt -w .
```

---

## 2. Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Exported types | `PascalCase` | `UserService` |
| Unexported types | `camelCase` | `userService` |
| Exported functions | `PascalCase` | `NewUserService` |
| Unexported functions | `camelCase` | `validateInput` |
| Constants | `PascalCase` | `MaxRetries` |
| Packages | `lowercase` | `handler`, `service` |
| Files | `snake_case.go` | `user_service.go` |
| Test files | `*_test.go` | `user_service_test.go` |
| Interfaces (1 method) | `-er` suffix | `Reader`, `Writer` |
| Receivers | 1-2 letters | `s`, `h`, `r`, `us` |

---

## 3. Error Handling

Always wrap errors with context:

```go
// GOOD
if err != nil {
    return fmt.Errorf("create user: %w", err)
}

// BAD - no context
if err != nil {
    return err
}

// BAD - loses error chain
if err != nil {
    return fmt.Errorf("create user: %v", err)
}
```

---

## 4. Package Design

- One package per directory
- Package name matches directory name
- Avoid `util`, `common`, `misc` packages
- Keep packages focused on a single responsibility
- No circular imports

```
internal/
  handler/    # HTTP handlers
  service/    # Business logic
  repository/ # Data access
  model/      # Domain types
  config/     # Configuration
```

---

## 5. Documentation

All exported types and functions MUST have godoc comments:

```go
// UserService manages user operations including
// creation, retrieval, and deletion.
type UserService interface {
    // GetUser returns a user by ID.
    // Returns ErrNotFound if the user does not exist.
    GetUser(ctx context.Context, id string) (*User, error)
}
```

Start comments with the name of the thing being documented.

---

## 6. Receiver Naming

Use short, consistent receiver names:

```go
// GOOD - short, consistent
func (s *userService) GetUser(ctx context.Context, id string) (*User, error) {}
func (s *userService) CreateUser(ctx context.Context, input CreateUserInput) (*User, error) {}

// BAD - long, inconsistent
func (svc *userService) GetUser(ctx context.Context, id string) (*User, error) {}
func (this *userService) CreateUser(ctx context.Context, input CreateUserInput) (*User, error) {}
```

---

## 7. Interface Size

Keep interfaces small. Prefer multiple small interfaces over one large one:

```go
// GOOD - small, focused interfaces
type Reader interface {
    Read(ctx context.Context, id string) (*User, error)
}

type Writer interface {
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
}

type ReadWriter interface {
    Reader
    Writer
}

// BAD - kitchen sink interface
type UserStore interface {
    Read(ctx context.Context, id string) (*User, error)
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id string) error
    List(ctx context.Context) ([]User, error)
    Search(ctx context.Context, query string) ([]User, error)
    Count(ctx context.Context) (int, error)
}
```

---

## 8. Context Propagation

Always pass `context.Context` as the first parameter for functions that do I/O:

```go
// GOOD
func (s *userService) GetUser(ctx context.Context, id string) (*User, error) {
    return s.repo.FindByID(ctx, id)
}

// BAD - no context
func (s *userService) GetUser(id string) (*User, error) {
    return s.repo.FindByID(context.Background(), id)
}
```

---

## 9. Struct Initialization

Always use field names in struct literals:

```go
// GOOD
user := User{
    Name:  "Alice",
    Email: "alice@example.com",
}

// BAD - positional
user := User{"Alice", "alice@example.com"}
```

---

## 10. golangci-lint

golangci-lint checks and enforces these rules:

```bash
# Check style
golangci-lint run ./...

# Auto-fix safe issues
golangci-lint run --fix ./...
```

All code MUST pass `golangci-lint run ./...` before it can be committed.

Recommended linters: `errcheck`, `govet`, `staticcheck`, `unused`, `gosimple`,
`ineffassign`, `gocritic`, `gofumpt`.
