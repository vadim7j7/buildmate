# Phoenix Framework Patterns

Reference patterns for Phoenix web development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Context Pattern

Bounded modules that serve as the public API for a business domain.

```elixir
defmodule MyApp.Accounts do
  @moduledoc "The Accounts context."

  alias MyApp.Repo
  alias MyApp.Accounts.User

  def list_users, do: Repo.all(User)

  def get_user(id) do
    case Repo.get(User, id) do
      nil -> {:error, :not_found}
      user -> {:ok, user}
    end
  end

  def create_user(attrs) do
    %User{}
    |> User.changeset(attrs)
    |> Repo.insert()
  end

  def update_user(%User{} = user, attrs) do
    user
    |> User.changeset(attrs)
    |> Repo.update()
  end

  def delete_user(%User{} = user), do: Repo.delete(user)
end
```

### Rules
- One context per business domain
- Contexts own their schemas
- Controllers call context functions, never Repo directly
- Return `{:ok, result}` or `{:error, reason}` from mutating functions

---

## 2. Ecto Schema Pattern

Define schemas with changesets for validation.

```elixir
defmodule MyApp.Accounts.User do
  use Ecto.Schema
  import Ecto.Changeset

  @type t :: %__MODULE__{}

  schema "users" do
    field :name, :string
    field :email, :string
    field :role, Ecto.Enum, values: [:admin, :user]
    has_many :posts, MyApp.Blog.Post
    timestamps()
  end

  def changeset(user, attrs) do
    user
    |> cast(attrs, [:name, :email, :role])
    |> validate_required([:name, :email])
    |> validate_format(:email, ~r/@/)
    |> unique_constraint(:email)
  end
end
```

---

## 3. Controller Pattern

JSON API controllers with action_fallback.

```elixir
defmodule MyAppWeb.UserController do
  use MyAppWeb, :controller

  alias MyApp.Accounts
  action_fallback MyAppWeb.FallbackController

  def index(conn, _params) do
    users = Accounts.list_users()
    render(conn, :index, users: users)
  end

  def create(conn, %{"user" => params}) do
    with {:ok, user} <- Accounts.create_user(params) do
      conn
      |> put_status(:created)
      |> render(:show, user: user)
    end
  end

  def show(conn, %{"id" => id}) do
    with {:ok, user} <- Accounts.get_user(id) do
      render(conn, :show, user: user)
    end
  end
end
```

### Rules
- Use `action_fallback` for centralized error handling
- Pattern match params in function heads
- Use `with` for multi-step operations
- Return `{:ok, data}` from `with` block

---

## 4. LiveView Pattern

Server-rendered interactive UI with Phoenix LiveView.

```elixir
defmodule MyAppWeb.UserLive.Index do
  use MyAppWeb, :live_view

  alias MyApp.Accounts

  @impl true
  def mount(_params, _session, socket) do
    {:ok, stream(socket, :users, Accounts.list_users())}
  end

  @impl true
  def handle_params(params, _url, socket) do
    {:noreply, apply_action(socket, socket.assigns.live_action, params)}
  end

  @impl true
  def handle_event("delete", %{"id" => id}, socket) do
    with {:ok, user} <- Accounts.get_user(id),
         {:ok, _} <- Accounts.delete_user(user) do
      {:noreply, stream_delete(socket, :users, user)}
    else
      {:error, :not_found} ->
        {:noreply, put_flash(socket, :error, "User not found")}

      {:error, %Ecto.Changeset{}} ->
        {:noreply, put_flash(socket, :error, "Could not delete user")}
    end
  end

  def handle_event("save", %{"user" => user_params}, socket) do
    case Accounts.create_user(user_params) do
      {:ok, user} ->
        {:noreply,
         socket
         |> put_flash(:info, "User created")
         |> stream_insert(:users, user)}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, :form, to_form(changeset))}
    end
  end

  defp apply_action(socket, :index, _params) do
    assign(socket, :page_title, "Users")
  end
end
```

### Rules
- Use `@impl true` on all callbacks
- `handle_event/3` must always return `{:noreply, socket}`: give every `with` an
  `else` (a bare `with` returns `{:error, _}` and crashes the LiveView)
- On `{:error, %Ecto.Changeset{}}` from a form, re-assign `to_form(changeset)` so
  the errors render; for other errors, `put_flash(socket, :error, ...)`
- Use streams for large collections
- Handle events with `handle_event/3`
- Use assigns for state management

---

## 5. Channel / PubSub Pattern

Real-time communication with channels and PubSub.

```elixir
# Channel
defmodule MyAppWeb.ChatChannel do
  use MyAppWeb, :channel

  @impl true
  def join("chat:" <> room_id, _params, socket) do
    {:ok, assign(socket, :room_id, room_id)}
  end

  @impl true
  def handle_in("message", %{"body" => body}, socket) do
    broadcast!(socket, "message", %{body: body})
    {:noreply, socket}
  end
end

# PubSub broadcast from context
defmodule MyApp.Chat do
  def send_message(room_id, message) do
    Phoenix.PubSub.broadcast(MyApp.PubSub, "chat:#{room_id}", {:new_message, message})
  end
end
```

---

## 6. Plug Pipeline Pattern

Request processing through plug pipelines.

```elixir
defmodule MyAppWeb.Plugs.Auth do
  import Plug.Conn

  def init(opts), do: opts

  def call(conn, _opts) do
    case get_req_header(conn, "authorization") do
      ["Bearer " <> token] ->
        case MyApp.Accounts.verify_token(token) do
          {:ok, user} -> assign(conn, :current_user, user)
          _ -> unauthorized(conn)
        end
      _ -> unauthorized(conn)
    end
  end

  defp unauthorized(conn) do
    conn
    |> put_status(:unauthorized)
    |> Phoenix.Controller.json(%{error: "unauthorized"})
    |> halt()
  end
end
```

### Health Check

The dev server is verified with `GET /health`; `mix phx.new` does not create it.

```elixir
# lib/my_app_web/controllers/health_controller.ex
defmodule MyAppWeb.HealthController do
  use MyAppWeb, :controller

  def show(conn, _params), do: json(conn, %{status: "ok"})
end

# lib/my_app_web/router.ex - outside every pipeline (no auth, no CSRF)
scope "/", MyAppWeb do
  get "/health", HealthController, :show
end
```

### Rules
- Implement `init/1` and `call/2`
- Use `halt()` to stop the pipeline
- Use `assign/3` to pass data to downstream plugs

---

## 7. Testing Pattern (ConnTest)

```elixir
defmodule MyAppWeb.UserControllerTest do
  use MyAppWeb.ConnCase, async: true

  alias MyApp.Accounts

  setup do
    {:ok, user} = Accounts.create_user(%{name: "Alice", email: "alice@test.com"})
    %{user: user}
  end

  describe "GET /api/users" do
    test "lists all users", %{conn: conn} do
      conn = get(conn, ~p"/api/users")
      assert json_response(conn, 200)["data"] |> length() == 1
    end
  end

  describe "POST /api/users" do
    test "creates user with valid params", %{conn: conn} do
      params = %{user: %{name: "Bob", email: "bob@test.com"}}
      conn = post(conn, ~p"/api/users", params)
      assert %{"name" => "Bob"} = json_response(conn, 201)["data"]
    end

    test "returns errors with invalid params", %{conn: conn} do
      conn = post(conn, ~p"/api/users", %{user: %{}})
      assert json_response(conn, 422)["errors"] != %{}
    end
  end
end
```

### Rules
- Use `ConnCase` for controller tests
- Use `~p` sigil for verified routes
- Use `json_response/2` for API tests
- Use `setup` for test data; use `*_fixture` helpers from `test/support/fixtures/`
  (what Phoenix generators create), not ExMachina
