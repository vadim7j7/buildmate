# Phoenix.PubSub

Broadcast domain events from contexts; LiveViews and channels subscribe and update.
The PubSub server is started in the application supervisor
(`{Phoenix.PubSub, name: MyApp.PubSub}`) before the Endpoint.

---

## 1. Broadcasting From the Context

The context owns the topic names and the message shapes; callers never build topic
strings themselves.

```elixir
defmodule MyApp.Blog do
  alias MyApp.Accounts.Scope

  @doc "Subscribe the caller to post changes visible to this scope."
  def subscribe_posts(%Scope{} = scope) do
    Phoenix.PubSub.subscribe(MyApp.PubSub, "user:#{scope.user.id}:posts")
  end

  defp broadcast(%Scope{} = scope, message) do
    Phoenix.PubSub.broadcast(MyApp.PubSub, "user:#{scope.user.id}:posts", message)
  end

  def create_post(%Scope{} = scope, attrs) do
    with {:ok, post} <- insert_post(scope, attrs) do
      broadcast(scope, {:created, post})
      {:ok, post}
    end
  end
end
```

- Broadcast **after** the transaction commits (outside `Repo.transaction`), or
  subscribers can read data that is rolled back
- Topics include the tenant or owner (`"user:42:posts"`, `"org:7:orders"`), so a
  subscriber only receives what its scope may see
- Messages are tagged tuples (`{:created, post}`, `{:deleted, post}`); keep them small
  (IDs or the struct, never large preloaded trees)

---

## 2. Subscribing in a LiveView

```elixir
def mount(_params, _session, socket) do
  scope = socket.assigns.current_scope
  if connected?(socket), do: Blog.subscribe_posts(scope)   # not during the static render
  {:ok, stream(socket, :posts, Blog.list_posts(scope))}
end

def handle_info({:created, post}, socket), do: {:noreply, stream_insert(socket, :posts, post, at: 0)}
def handle_info({:updated, post}, socket), do: {:noreply, stream_insert(socket, :posts, post)}
def handle_info({:deleted, post}, socket), do: {:noreply, stream_delete(socket, :posts, post)}
```

- Subscribe only when `connected?(socket)`: the first (dead) render would subscribe a
  process that exits immediately
- No unsubscribe needed: subscriptions end with the LiveView process
- Handle every message shape the topic carries, or the LiveView crashes on an unmatched
  `handle_info/2`

---

## 3. Channels and Presence

- Channels: `MyAppWeb.Endpoint.broadcast!/3` or `broadcast_from!/4` (skips the sender) to
  push to a channel topic; authorize the topic in `join/3` against the socket's user
- `Phoenix.Presence` for "who is online": track in the LiveView/channel, read with
  `Presence.list/1`; do not build presence yourself on top of PubSub

---

## 4. Testing

```elixir
test "create_post broadcasts", %{scope: scope} do
  Blog.subscribe_posts(scope)
  {:ok, post} = Blog.create_post(scope, %{title: "Hi", body: "..."})
  assert_receive {:created, ^post}
end
```

In LiveView tests, broadcast or call the context and then assert on `render(view)`.

---

## Rules

- `Phoenix.PubSub` is for in-cluster notifications; it does not persist messages. Work
  that must not be lost goes through a job queue (Oban, see `/new-job`)
- Topic names and message tuples are defined once, in the context
- Never broadcast secrets or data the subscriber's scope may not see
