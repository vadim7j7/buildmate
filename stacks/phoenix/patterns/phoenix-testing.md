# Phoenix Testing (ConnCase, LiveViewTest)

Web-layer tests for Phoenix. General ExUnit, Mox and StreamData rules are in
`testing.md`; context tests use `MyApp.DataCase` as shown there.

---

## 1. Case Templates

- `MyAppWeb.ConnCase` (`test/support/conn_case.ex`): builds `conn`, checks out the Ecto
  sandbox, imports `Phoenix.ConnTest`, `Phoenix.LiveViewTest` helpers and verified routes
  (`~p"/..."`)
- `MyApp.DataCase`: contexts and schemas, with `errors_on/1`
- After `mix phx.gen.auth`, ConnCase also has `register_and_log_in_user/1`, which adds a
  logged-in `conn`, the `user` and the `scope` to the test context

```elixir
setup :register_and_log_in_user
```

---

## 2. Controller / JSON Tests

```elixir
defmodule MyAppWeb.PostControllerTest do
  use MyAppWeb.ConnCase, async: true

  import MyApp.BlogFixtures

  setup :register_and_log_in_user

  describe "GET /api/posts" do
    test "lists only the user's posts", %{conn: conn, scope: scope} do
      mine = post_fixture(scope)
      other_scope = MyApp.Accounts.Scope.for_user(MyApp.AccountsFixtures.user_fixture())
      _other = post_fixture(other_scope)

      conn = get(conn, ~p"/api/posts")

      assert [%{"id" => id}] = json_response(conn, 200)["data"]
      assert id == mine.id
    end
  end

  describe "POST /api/posts" do
    test "422 with field errors on invalid data", %{conn: conn} do
      conn = post(conn, ~p"/api/posts", post: %{title: ""})
      assert %{"title" => ["can't be blank"]} = json_response(conn, 422)["errors"]
    end
  end

  test "401 when logged out" do
    conn = get(build_conn(), ~p"/api/posts")
    assert json_response(conn, 401)
  end
end
```

HTML: `html_response(conn, 200) =~ "Posts"`, `redirected_to(conn) == ~p"/users/log-in"`.

---

## 3. LiveView Tests

```elixir
defmodule MyAppWeb.PostLiveTest do
  use MyAppWeb.ConnCase, async: true

  import Phoenix.LiveViewTest
  import MyApp.BlogFixtures

  setup :register_and_log_in_user

  test "creates a post", %{conn: conn} do
    {:ok, view, _html} = live(conn, ~p"/posts/new")

    assert view
           |> form("#post-form", post: %{title: ""})
           |> render_change() =~ "can&#39;t be blank"

    {:ok, _view, html} =
      view
      |> form("#post-form", post: %{title: "Hello", body: "World"})
      |> render_submit()
      |> follow_redirect(conn, ~p"/posts")

    assert html =~ "Hello"
  end

  test "deletes from the list", %{conn: conn, scope: scope} do
    post = post_fixture(scope)
    {:ok, view, _html} = live(conn, ~p"/posts")

    view |> element("#posts-#{post.id} a", "Delete") |> render_click()

    refute has_element?(view, "#posts-#{post.id}")
  end

  test "redirects when logged out" do
    assert {:error, {:redirect, %{to: path}}} = live(build_conn(), ~p"/posts")
    assert path =~ "/log-in"
  end
end
```

- Select elements by DOM id (`#post-form`, `#posts-123`); give the template stable ids
  rather than matching on CSS classes or copy
- `has_element?/3` for presence, `render(view) =~` for text; avoid asserting large HTML
- PubSub-driven updates: trigger the context function, then `assert render(view) =~ ...`
- Uploads: `file_input/4` + `render_upload/2`; hooks: `render_hook/3`

---

## 4. Channel Tests

```elixir
use MyAppWeb.ChannelCase

{:ok, _reply, socket} =
  MyAppWeb.UserSocket
  |> socket("user_id", %{current_scope: scope})
  |> subscribe_and_join(MyAppWeb.RoomChannel, "room:lobby")

push(socket, "new_msg", %{"body" => "hi"})
assert_broadcast "new_msg", %{body: "hi"}
```

---

## Rules

- Test through the router (`get/post/live`), not by calling controller functions
- Every protected route has a logged-out test and an other-user's-record test
- `async: true` with the Ecto sandbox; processes started by the test that hit the DB
  need sandbox `allow/3`
- Fixtures go through context functions, so tests exercise the same validation as the app
- Oban jobs: `use Oban.Testing, repo: MyApp.Repo` and `assert_enqueued/1`, `perform_job/2`
  (see `/new-job`)
