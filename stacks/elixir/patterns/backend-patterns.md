# Elixir Code Patterns

Reference patterns for Elixir development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. GenServer Pattern

Use GenServer for stateful processes with client/server separation.

```elixir
defmodule MyApp.Counter do
  @moduledoc """
  A simple counter process using GenServer.
  """
  use GenServer

  # Client API

  @doc "Starts the counter with an initial value."
  def start_link(opts \\ []) do
    initial = Keyword.get(opts, :initial, 0)
    name = Keyword.get(opts, :name, __MODULE__)
    GenServer.start_link(__MODULE__, initial, name: name)
  end

  @doc "Gets the current count."
  @spec get(GenServer.server()) :: integer()
  def get(server \\ __MODULE__) do
    GenServer.call(server, :get)
  end

  @doc "Increments the counter by the given amount."
  @spec increment(GenServer.server(), integer()) :: :ok
  def increment(server \\ __MODULE__, amount \\ 1) do
    GenServer.cast(server, {:increment, amount})
  end

  # Server callbacks

  @impl true
  def init(initial) do
    {:ok, initial}
  end

  @impl true
  def handle_call(:get, _from, count) do
    {:reply, count, count}
  end

  @impl true
  def handle_cast({:increment, amount}, count) do
    {:noreply, count + amount}
  end
end
```

### GenServer Rules

- Separate client API (public functions) from server callbacks
- Use `@impl true` on all callbacks
- Client functions call GenServer.call/cast
- Use `start_link` with keyword options
- Name the process via `:name` option for singleton use

---

## 2. Supervisor Tree Pattern

Organize processes into supervision trees.

```elixir
defmodule MyApp.Workers.Supervisor do
  @moduledoc """
  Supervises background worker processes.
  """
  use Supervisor

  def start_link(init_arg) do
    Supervisor.start_link(__MODULE__, init_arg, name: __MODULE__)
  end

  @impl true
  def init(_init_arg) do
    children = [
      {MyApp.Workers.EmailSender, []},
      {MyApp.Workers.DataProcessor, pool_size: 5},
      {Task.Supervisor, name: MyApp.Workers.TaskSupervisor}
    ]

    Supervisor.init(children, strategy: :one_for_one)
  end
end
```

### Supervisor Rules

- Use `:one_for_one` unless processes are dependent
- Use `:one_for_all` when all children must restart together
- Use `:rest_for_one` for ordered dependencies
- Include `Task.Supervisor` for fire-and-forget tasks
- Define child specs in the child module when possible

---

## 3. Pipeline Pattern

Use the pipe operator for data transformations.

```elixir
def process_order(params) do
  params
  |> validate_params()
  |> fetch_user()
  |> calculate_total()
  |> apply_discount()
  |> create_order()
  |> send_confirmation()
end

# Each function returns {:ok, data} or {:error, reason}
# Use with for fallible pipelines:

def process_order(params) do
  with {:ok, valid_params} <- validate_params(params),
       {:ok, user} <- fetch_user(valid_params.user_id),
       {:ok, total} <- calculate_total(valid_params.items),
       {:ok, order} <- create_order(user, total) do
    send_confirmation(order)
    {:ok, order}
  end
end
```

### Pipeline Rules

- Use `|>` for data flowing through transformations
- First argument is piped, keep it consistent
- Use `with` when steps may fail
- Each step in a `with` returns `{:ok, _}` or `{:error, _}`

---

## 4. Context / Boundary Pattern

Organize business logic into contexts (bounded modules).

```elixir
defmodule MyApp.Accounts do
  @moduledoc """
  The Accounts context. Handles user accounts and authentication.
  """

  alias MyApp.Repo
  alias MyApp.Accounts.{User, Credential}

  @doc "Returns all users."
  @spec list_users() :: [User.t()]
  def list_users, do: Repo.all(User)

  @doc "Gets a user by ID."
  @spec get_user(String.t()) :: {:ok, User.t()} | {:error, :not_found}
  def get_user(id) do
    case Repo.get(User, id) do
      nil -> {:error, :not_found}
      user -> {:ok, user}
    end
  end

  @doc "Creates a user with the given attributes."
  @spec create_user(map()) :: {:ok, User.t()} | {:error, Ecto.Changeset.t()}
  def create_user(attrs) do
    %User{}
    |> User.changeset(attrs)
    |> Repo.insert()
  end

  @doc "Authenticates a user by email and password."
  @spec authenticate(String.t(), String.t()) :: {:ok, User.t()} | {:error, :invalid_credentials}
  def authenticate(email, password) do
    with {:ok, user} <- get_user_by_email(email),
         true <- Credential.verify(user.credential, password) do
      {:ok, user}
    else
      _ -> {:error, :invalid_credentials}
    end
  end
end
```

### Context Rules

- One context per business domain
- Contexts are the public API for a domain
- Internal modules (schemas, queries) are private to the context
- Other contexts call through the public API, never access internal modules

---

## 5. Error Handling Pattern

Use ok/error tuples and `with` for composable error handling.

```elixir
# Pattern 1: Simple ok/error
def get_user(id) do
  case Repo.get(User, id) do
    nil -> {:error, :not_found}
    user -> {:ok, user}
  end
end

# Pattern 2: with for multi-step
def transfer_funds(from_id, to_id, amount) do
  with {:ok, from} <- get_account(from_id),
       {:ok, to} <- get_account(to_id),
       :ok <- validate_balance(from, amount),
       {:ok, _} <- debit(from, amount),
       {:ok, _} <- credit(to, amount) do
    {:ok, :transferred}
  end
end

# Pattern 3: Custom error types
defmodule MyApp.Error do
  defexception [:code, :message]

  def not_found(resource, id) do
    %__MODULE__{code: :not_found, message: "#{resource} not found: #{id}"}
  end

  def validation(message) do
    %__MODULE__{code: :validation, message: message}
  end
end
```

### Error Rules

- Return `{:ok, result}` or `{:error, reason}` from fallible functions
- Use `with` for composing multiple fallible steps
- Use atoms for error reasons: `:not_found`, `:unauthorized`, `:validation`
- Use `!` suffix functions (`get_user!`) when you want to raise on failure
- Never rescue broadly; rescue specific exceptions

---

## 6. Testing Patterns

### ExUnit Test

```elixir
defmodule MyApp.AccountsTest do
  use MyApp.DataCase, async: true

  alias MyApp.Accounts

  describe "create_user/1" do
    test "creates user with valid attributes" do
      attrs = %{name: "Alice", email: "alice@example.com"}
      assert {:ok, user} = Accounts.create_user(attrs)
      assert user.name == "Alice"
    end

    test "returns error with invalid attributes" do
      assert {:error, changeset} = Accounts.create_user(%{})
      assert %{name: ["can't be blank"]} = errors_on(changeset)
    end
  end
end
```

### GenServer Test

```elixir
defmodule MyApp.CacheTest do
  use ExUnit.Case, async: true

  setup do
    cache = start_supervised!(MyApp.Cache)
    %{cache: cache}
  end

  test "round-trip put/get", %{cache: cache} do
    MyApp.Cache.put(cache, :key, "value")
    assert MyApp.Cache.get(cache, :key) == "value"
  end
end
```

### Test Rules

- Use `async: true` when tests don't share state
- Use `describe` blocks matching `"function_name/arity"`
- Pattern match assertions: `assert {:ok, %User{}} = result`
- Use `start_supervised!` for process tests (auto-cleanup)
- Use Mox for behavior-based mocking
