# Elixir Testing

ExUnit for everything, Mox for mocks at behaviour boundaries, StreamData for
property tests. Extends the short testing section in `backend-patterns.md`.

```bash
mix test                                  # all
mix test test/my_app/accounts_test.exs:42 # one test by line
mix test --failed                         # re-run last failures
mix test --only integration               # tagged tests (@tag :integration / @moduletag)
mix test --warnings-as-errors             # CI
```

---

## 1. Dependencies

Mox and StreamData are not part of Elixir; add them to `mix.exs` if missing (check
`mix.exs` first, and keep the versions already there):

```elixir
defp deps do
  [
    {:mox, "~> 1.2", only: :test},
    {:stream_data, "~> 1.1", only: [:dev, :test]}
  ]
end
```

Then `mix deps.get`.

---

## 2. ExUnit Structure

```elixir
defmodule MyApp.PricingTest do
  use ExUnit.Case, async: true

  doctest MyApp.Pricing   # runs the iex> examples in @doc

  describe "total/1" do
    setup do
      %{items: [%{price: 100, qty: 2}, %{price: 50, qty: 1}]}
    end

    test "sums price times quantity", %{items: items} do
      assert MyApp.Pricing.total(items) == 250
    end

    test "empty cart is zero" do
      assert MyApp.Pricing.total([]) == 0
    end
  end
end
```

- `async: true` unless the test touches global state (named processes, `Application`
  env, ETS tables owned elsewhere, SQLite DB)
- `describe "fun/arity"`, one behaviour per `test`
- Pattern-match results: `assert {:error, :not_found} = Accounts.fetch(id)`
- `assert_raise ArgumentError, fn -> ... end` only for real exceptions; most failures are
  `{:error, _}` tuples
- Processes: `start_supervised!/1` (stopped after the test); `assert_receive msg, 500`
  instead of `Process.sleep`
- Temporary config: change it in `setup` and restore with `on_exit/1`, and make the test
  `async: false`

---

## 3. Mox (mocks for behaviours)

Mox mocks only behaviours, which forces a real contract at the boundary (HTTP clients,
mailers, payment gateways). Never mock your own contexts.

```elixir
# lib/my_app/weather.ex
defmodule MyApp.Weather do
  @callback fetch(city :: String.t()) :: {:ok, map()} | {:error, term()}

  def fetch(city), do: impl().fetch(city)
  defp impl, do: Application.get_env(:my_app, :weather_client, MyApp.Weather.HTTP)
end

# test/test_helper.exs
Mox.defmock(MyApp.Weather.Mock, for: MyApp.Weather)
Application.put_env(:my_app, :weather_client, MyApp.Weather.Mock)

# test/my_app/forecast_test.exs
defmodule MyApp.ForecastTest do
  use ExUnit.Case, async: true
  import Mox

  setup :verify_on_exit!

  test "reports rain" do
    expect(MyApp.Weather.Mock, :fetch, fn "Oslo" -> {:ok, %{"rain" => true}} end)
    assert MyApp.Forecast.umbrella?("Oslo")
  end
end
```

- `expect/4` = must be called (n times); `stub/3` = may be called
- Mox expectations belong to the test process. If the code under test calls the mock from
  another process (Task, GenServer), allow it with `allow(Mock, self(), pid)` or use
  `setup :set_mox_from_context` with `async: false`

---

## 4. StreamData (property-based tests)

For pure functions with a clear invariant (encode/decode round-trips, sorting,
parsers, money math).

```elixir
defmodule MyApp.SlugTest do
  use ExUnit.Case, async: true
  use ExUnitProperties

  property "slugs contain only lowercase letters, digits and dashes" do
    check all title <- string(:printable, max_length: 200) do
      assert MyApp.Slug.from(title) =~ ~r/\A[a-z0-9-]*\z/
    end
  end

  property "encode/decode round-trips" do
    check all map <- map_of(string(:alphanumeric), integer()) do
      assert map |> MyApp.Codec.encode() |> MyApp.Codec.decode() == {:ok, map}
    end
  end
end
```

- A failing property shrinks to the smallest counter-example: add it as a plain `test`
- Keep generators bounded (`max_length`, `max_runs: 100` by default) so the suite stays fast

---

## 5. Database Tests (Ecto)

`MyApp.DataCase` checks out an `Ecto.Adapters.SQL.Sandbox` connection per test; each
test runs in a transaction that is rolled back. Build data with small fixture
functions (`test/support/fixtures/*_fixtures.ex`) or ExMachina if the project uses it.

```elixir
def user_fixture(attrs \\ %{}) do
  {:ok, user} =
    attrs
    |> Enum.into(%{email: "user#{System.unique_integer([:positive])}@example.com", name: "Ann"})
    |> MyApp.Accounts.create_user()

  user
end
```

- Unique values from `System.unique_integer/1`, never fixed emails (unique indexes)
- Processes that touch the DB (Tasks, GenServers) need `Ecto.Adapters.SQL.Sandbox.allow/3`
  or shared mode (`async: false`)

---

## Rules

- Every bug fix starts with a failing test
- No `Process.sleep` for synchronisation: `assert_receive`, monitors, or `:sys.get_state/1`
- Test public functions; private ones are covered through them
- `mix test --warnings-as-errors` must pass
