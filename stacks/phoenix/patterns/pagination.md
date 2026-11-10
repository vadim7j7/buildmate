# Pagination (Ecto + Phoenix)

Offset pagination for small lists and admin pages; keyset (cursor) pagination for
large tables, infinite scroll and public APIs. If the project already uses a library
(Flop, Scrivener, Paginator), follow it.

---

## 1. Params, Clamped

```elixir
@default_per_page 25
@max_per_page 100

def page_params(params) do
  page = parse_pos_int(params["page"], 1)
  per_page = params["per_page"] |> parse_pos_int(@default_per_page) |> min(@max_per_page)
  %{page: page, per_page: per_page}
end

defp parse_pos_int(nil, default), do: default

defp parse_pos_int(value, default) do
  case Integer.parse(value) do
    {n, ""} when n > 0 -> n
    _ -> default
  end
end
```

---

## 2. Offset Pagination (in the context)

```elixir
def list_posts(%Scope{} = scope, %{page: page, per_page: per_page}) do
  base = from p in Post, where: p.user_id == ^scope.user.id

  entries =
    base
    |> order_by([p], desc: p.inserted_at, desc: p.id)   # unique tiebreaker
    |> limit(^per_page)
    |> offset(^((page - 1) * per_page))
    |> Repo.all()

  %{entries: entries, page: page, per_page: per_page, total: Repo.aggregate(base, :count)}
end
```

JSON: `%{data: ..., meta: %{page: 2, per_page: 25, total: 312}}`; keyset responses send
`meta: %{next_cursor: Blog.encode_cursor(next)}`.

- Deterministic `order_by` ending in the primary key
- Large offsets are slow; `count` on big tables is slow: drop `total` or switch to keyset

---

## 3. Keyset (Cursor) Pagination

```elixir
def list_posts_after(%Scope{} = scope, cursor, per_page) do
  query =
    from p in Post,
      where: p.user_id == ^scope.user.id,
      order_by: [desc: p.inserted_at, desc: p.id],
      limit: ^(per_page + 1)                               # one extra row = has_more

  query =
    case cursor do
      nil -> query
      {at, id} -> where(query, [p], p.inserted_at < ^at or (p.inserted_at == ^at and p.id < ^id))
    end

  rows = Repo.all(query)
  {entries, rest} = Enum.split(rows, per_page)
  last = List.last(entries)
  %{entries: entries, next: if(rest != [], do: {last.inserted_at, last.id})}
end

# The API layer turns `next` into an opaque string and back.
def encode_cursor(nil), do: nil
def encode_cursor({at, id}), do: Base.url_encode64("#{DateTime.to_iso8601(at)}|#{id}", padding: false)

def decode_cursor(nil), do: {:ok, nil}

def decode_cursor(token) do
  with {:ok, raw} <- Base.url_decode64(token, padding: false),
       [at, id] <- String.split(raw, "|", parts: 2),
       {:ok, at, _} <- DateTime.from_iso8601(at),
       {id, ""} <- Integer.parse(id) do
    {:ok, {at, id}}
  else
    _ -> {:error, :invalid_cursor}   # 400, not a crash
  end
end
```

This assumes `timestamps(type: :utc_datetime_usec)`; with `:naive_datetime` use
`NaiveDateTime` in the encoder and decoder. Index the sort columns:
`create index(:posts, [:user_id, :inserted_at, :id])`.

---

## 4. LiveView: Streams and Infinite Scroll

```elixir
def mount(_params, _session, socket) do
  {:ok, socket |> assign(cursor: nil, end?: false) |> stream(:posts, []) |> load_more()}
end

def handle_event("load-more", _params, socket), do: {:noreply, load_more(socket)}

defp load_more(%{assigns: %{end?: true}} = socket), do: socket

defp load_more(socket) do
  %{entries: posts, next: next} =
    Blog.list_posts_after(socket.assigns.current_scope, socket.assigns.cursor, 25)

  socket
  |> stream(:posts, posts)                        # appends; nothing kept in assigns
  |> assign(cursor: next, end?: is_nil(next))
end
```

```heex
<div id="posts" phx-update="stream" phx-viewport-bottom={!@end? && "load-more"}>
  <div :for={{dom_id, post} <- @streams.posts} id={dom_id}>{post.title}</div>
</div>
```

---

## Rules

- Every list endpoint and LiveView list is paginated, with a server-side maximum
- Pagination runs in the context (with the scope), not in the controller
- An invalid cursor or page is a 400 / ignored, never a 500
- LiveView lists use streams, so the server does not hold every loaded row in memory
