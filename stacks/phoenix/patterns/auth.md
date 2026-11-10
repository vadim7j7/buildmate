# Phoenix Authentication and Scopes

Use the generator, `mix phx.gen.auth`, and extend what it creates; do not hand-roll
sessions, password hashing or token handling. Phoenix 1.8 generates **scopes**: the
signed-in user travels as `current_scope` (a `%MyApp.Accounts.Scope{}`), not as a bare
`current_user`, and every context function takes the scope first.

---

## 1. Generating

```bash
mix phx.gen.auth Accounts User users            # asks LiveView or controllers
mix phx.gen.auth Accounts User users --live     # LiveView pages
mix deps.get && mix ecto.migrate
```

It generates the `Accounts` context with `User` and `UserToken`, `MyAppWeb.UserAuth`
(plugs and LiveView `on_mount` hooks), login/registration/settings pages, magic-link
(email) login, and `MyApp.Accounts.Scope`. Passwords are hashed with bcrypt by default
(`--hashing-lib argon2` or `pbkdf2` to change). Read the generated `user_auth.ex` and
`scope.ex` before writing auth code: names below are the generator's defaults.

If the project already has auth (look for `UserAuth`, `Guardian`, `Pow`, `current_user`),
follow it instead.

---

## 2. The Scope

```elixir
defmodule MyApp.Accounts.Scope do
  alias MyApp.Accounts.User

  defstruct user: nil

  def for_user(%User{} = user), do: %__MODULE__{user: user}
  def for_user(nil), do: nil
end
```

Add fields here when the app needs more than the user (organization, role); fill them
in a plug / `on_mount` hook after the scope is built.

---

## 3. Router

```elixir
pipeline :browser do
  # ... generated plugs
  plug :fetch_current_scope_for_user     # sets conn.assigns.current_scope (or nil)
end

scope "/", MyAppWeb do
  pipe_through [:browser, :require_authenticated_user]

  live_session :require_authenticated_user,
    on_mount: [{MyAppWeb.UserAuth, :require_authenticated}] do
    live "/posts", PostLive.Index, :index
    live "/posts/:id", PostLive.Show, :show
  end
end
```

The hook names come from `UserAuth.on_mount/4` in your project (current generators use
`:require_authenticated` and `:mount_current_scope`); check the clauses there. Every
`live` route that needs a user must be in a `live_session` with the authenticating hook:
the plug pipeline only runs on the first HTTP request, not on live navigation.

Sensitive actions (change email or password) use the generated sudo-mode check (recent
login required); keep it on any new sensitive page.

---

## 4. Context Functions Take the Scope

Authorization lives in the context, by filtering on the scope, so a forgotten check in
a LiveView cannot leak another user's records.

```elixir
defmodule MyApp.Blog do
  import Ecto.Query
  alias MyApp.Accounts.Scope
  alias MyApp.Blog.Post
  alias MyApp.Repo

  def list_posts(%Scope{} = scope) do
    Repo.all(from p in Post, where: p.user_id == ^scope.user.id, order_by: [desc: p.inserted_at])
  end

  def get_post!(%Scope{} = scope, id) do
    Repo.get_by!(Post, id: id, user_id: scope.user.id)   # 404 for other users' posts
  end

  def create_post(%Scope{} = scope, attrs) do
    %Post{}
    |> Post.changeset(attrs, scope)                       # changeset sets user_id from scope
    |> Repo.insert()
  end
end
```

```elixir
# LiveView
def mount(_params, _session, socket) do
  {:ok, stream(socket, :posts, Blog.list_posts(socket.assigns.current_scope))}
end

# Controller
def index(conn, _params) do
  render(conn, :index, posts: Blog.list_posts(conn.assigns.current_scope))
end
```

With a default scope configured (`phx.gen.auth` sets it), `mix phx.gen.live`,
`phx.gen.html`, `phx.gen.json`, `phx.gen.context` and `phx.gen.schema` generate scoped
code like this: prefer them for new resources.

---

## 5. JSON APIs

`phx.gen.auth` targets browser sessions. For an API used by other clients, issue tokens
with the generated `UserToken` machinery (or `Phoenix.Token` for short-lived signed
tokens), verify them in an `:api` pipeline plug that assigns `current_scope`, and return
`401` with a fixed JSON body on failure.

---

## Rules

- `user_id` (owner) is set from the scope in the changeset, never cast from params
- Every query for user-owned data filters by the scope; fetch with `get_by!` on id + owner
- Templates and LiveViews read `@current_scope` (`@current_scope.user`), not `@current_user`
- Never log tokens, session contents or passwords; keep `:password` in `filter_parameters`
- Tests: use the generated `register_and_log_in_user` setup (see `phoenix-testing.md`)
