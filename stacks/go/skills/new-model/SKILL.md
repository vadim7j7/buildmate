---
name: new-model
description: Generate a Go struct model with database tags and repository
---

# /new-model

## What This Does

Generates a Go struct model for database operations with JSON/DB tags, a repository
interface, and test file.

## Usage

```
/new-model User                  # Creates internal/model/user.go
/new-model Article               # Creates internal/model/article.go
/new-model OrderItem             # Creates internal/model/order_item.go
```

## How It Works

1. **Read reference patterns.** Load the model pattern from:
   - Existing models in `internal/model/`
   - `patterns/backend-patterns.md`
   - `styles/backend-go.md`

2. **Determine model name.** Parse the argument to determine the struct name:
   - `User` becomes `User` struct in `internal/model/user.go`
   - `OrderItem` becomes `OrderItem` struct in `internal/model/order_item.go`

3. **Generate the model file.** Create the struct with:
   - JSON tags (`json:"field_name"`)
   - DB tags (`db:"field_name"`) for sqlc/sqlx
   - Standard `ID`, `CreatedAt`, `UpdatedAt` fields
   - Typed fields with proper Go types
   - Godoc comment on the struct

4. **Generate the repository interface.**

   ```go
   type UserRepository interface {
       FindAll(ctx context.Context) ([]User, error)
       FindByID(ctx context.Context, id string) (*User, error)
       Create(ctx context.Context, user *User) error
       Update(ctx context.Context, user *User) error
       Delete(ctx context.Context, id string) error
   }
   ```

5. **Generate the test file.** Create tests with:
   - Table-driven tests for repository operations
   - Mock repository implementation

6. **Run quality checks.**

   ```bash
   gofmt -w <generated_files>
   golangci-lint run <generated_files>
   go test ./internal/model/...
   ```

## Generated Files

```
internal/model/<name>.go
internal/model/<name>_test.go
internal/repository/<name>_repository.go  (interface)
```
