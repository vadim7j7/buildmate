# Elixir Style Guide

Mandatory style rules for all Elixir code in this project. These are enforced by
mix format, Credo, Dialyzer, and code review.

---

## 1. Pipe Operator

Use the pipe operator for data transformation chains:

```elixir
# GOOD
result =
  data
  |> parse()
  |> validate()
  |> transform()

# BAD
result = transform(validate(parse(data)))
```

Don't pipe into single function calls or use pipe for side effects only.

---

## 2. Pattern Matching

Use pattern matching in function heads instead of conditionals:

```elixir
# GOOD
def handle_result({:ok, data}), do: process(data)
def handle_result({:error, reason}), do: log_error(reason)

# BAD
def handle_result(result) do
  if elem(result, 0) == :ok do
    process(elem(result, 1))
  else
    log_error(elem(result, 1))
  end
end
```

---

## 3. Module Structure

Organize modules in this order:

```elixir
defmodule MyApp.Users.User do
  @moduledoc """
  Represents a user in the system.
  """

  use Ecto.Schema
  import Ecto.Changeset

  # 1. Module attributes
  @primary_key {:id, :binary_id, autogenerate: true}
  @required_fields [:name, :email]

  # 2. Schema / struct
  schema "users" do
    field :name, :string
    field :email, :string
    timestamps()
  end

  # 3. Type definitions
  @type t :: %__MODULE__{}

  # 4. Public functions
  @doc "Creates a changeset for user creation."
  @spec changeset(t(), map()) :: Ecto.Changeset.t()
  def changeset(user, attrs) do
    user
    |> cast(attrs, @required_fields)
    |> validate_required(@required_fields)
    |> unique_constraint(:email)
  end

  # 5. Private functions
end
```

---

## 4. Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Modules | `PascalCase` | `MyApp.UserService` |
| Functions | `snake_case` | `get_user` |
| Variables | `snake_case` | `user_name` |
| Atoms | `snake_case` | `:not_found` |
| Constants | `@snake_case` | `@max_retries` |
| Predicates | `snake_case?` | `valid?` |
| Dangerous | `snake_case!` | `get_user!` |
| Files | `snake_case.ex` | `user_service.ex` |
| Test files | `*_test.exs` | `user_service_test.exs` |

---

## 5. Guard Clauses

Use guards for type and value checks in function heads:

```elixir
# GOOD
def process(value) when is_binary(value), do: String.upcase(value)
def process(value) when is_integer(value), do: value * 2
def process(_value), do: {:error, :invalid_type}

# BAD
def process(value) do
  cond do
    is_binary(value) -> String.upcase(value)
    is_integer(value) -> value * 2
    true -> {:error, :invalid_type}
  end
end
```

---

## 6. With Expressions

Use `with` for multi-step operations that may fail:

```elixir
# GOOD
def create_order(params) do
  with {:ok, user} <- fetch_user(params.user_id),
       {:ok, items} <- validate_items(params.items),
       {:ok, order} <- insert_order(user, items) do
    {:ok, order}
  end
end

# BAD - nested case
def create_order(params) do
  case fetch_user(params.user_id) do
    {:ok, user} ->
      case validate_items(params.items) do
        {:ok, items} ->
          insert_order(user, items)
        error -> error
      end
    error -> error
  end
end
```

---

## 7. Documentation

All modules and public functions MUST have documentation:

```elixir
@moduledoc """
Handles user authentication and session management.
"""

@doc """
Authenticates a user by email and password.

Returns `{:ok, user}` on success, `{:error, :invalid_credentials}` on failure.

## Examples

    iex> authenticate("alice@example.com", "password123")
    {:ok, %User{}}

    iex> authenticate("alice@example.com", "wrong")
    {:error, :invalid_credentials}
"""
@spec authenticate(String.t(), String.t()) :: {:ok, User.t()} | {:error, :invalid_credentials}
def authenticate(email, password) do
  # ...
end
```

---

## 8. Credo Rules

Credo enforces style consistency:

```bash
# Check style
mix credo --strict

# Check specific file
mix credo --strict lib/my_app/users.ex
```

Key Credo checks:
- Module documentation required
- Pipe chains start with raw value
- No nested `if/case/cond`
- Consistent parameter ordering
- No `unless` with `else`

---

## 9. Dialyzer Typespecs

All public functions MUST have `@spec`:

```elixir
@spec get_user(String.t()) :: {:ok, User.t()} | {:error, :not_found}
def get_user(id) do
  # ...
end

@spec list_users(keyword()) :: [User.t()]
def list_users(opts \\ []) do
  # ...
end
```

Run Dialyzer to verify:

```bash
mix dialyzer
```

---

## 10. List Comprehensions

Use `for` comprehensions for mapping and filtering:

```elixir
# GOOD - comprehension with filter
for user <- users, user.active?, do: user.email

# GOOD - comprehension with pattern matching
for {:ok, value} <- results, do: value

# Also good - Enum functions for simple cases
Enum.map(users, & &1.email)
Enum.filter(users, & &1.active?)
```

---

## 11. mix format Enforcement

All code MUST be formatted with `mix format`:

```bash
# Format all files
mix format

# Check formatting without changing files
mix format --check-formatted
```

All code MUST pass `mix format --check-formatted` before it can be committed.
