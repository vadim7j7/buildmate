---
name: new-test
description: Write ExUnit tests for a module, GenServer or context (Mox/StreamData where they fit)
---

# /new-test

## What This Does

Writes or extends the ExUnit test file for an existing module: unit tests per
public function, process tests for GenServers, Mox mocks at behaviour boundaries and
property tests for pure functions with an invariant.

## Usage

```
/new-test lib/my_app/pricing.ex            # module tests
/new-test MyApp.Cache                      # GenServer tests
/new-test MyApp.Accounts.create_user/1     # one function
```

## How It Works

1. **Read** `.claude/patterns/testing.md`, `.claude/patterns/backend-patterns.md` and the
   code under test. Look at `test/support/` (DataCase, ConnCase, fixtures) and the
   existing tests for the same module; extend the file if it exists.
2. **Map the file**: `lib/my_app/foo/bar.ex` -> `test/my_app/foo/bar_test.exs`,
   module `MyApp.Foo.BarTest`.
3. **List the cases** per public function: happy path, each `{:error, _}` branch,
   edge inputs (empty, nil, boundary values). Skip private functions.
4. **Pick the case template**:
   - Pure module: `use ExUnit.Case, async: true` (+ `doctest` if it has `iex>` examples)
   - Ecto context: `use MyApp.DataCase, async: true` (SQLite: `async: false`)
   - Phoenix controller / LiveView: `use MyAppWeb.ConnCase` (see `phoenix-testing.md`
     when the project is a Phoenix app)
   - GenServer: `start_supervised!/1` in `setup`, then drive the public API
5. **Choose the doubles**: external services behind a behaviour get a Mox mock
   (`Mox.defmock` in `test/test_helper.exs`, `setup :verify_on_exit!`). Invariants on
   pure functions get a `property` with StreamData. If `:mox` or `:stream_data` is not in
   `mix.exs`, add it (see `testing.md`) and run `mix deps.get`.
6. **Write the tests**: `describe "fun/arity"`, pattern-matching assertions,
   `assert_receive` instead of sleeps.
7. **Run** the new file (`mix test test/my_app/foo/bar_test.exs`), then the quality gates:
   `mix format`, `mix compile --warnings-as-errors`, `mix test`.

## Rules

- A test must fail if the behaviour it names breaks: assert outcomes, not just `:ok`
- No `Process.sleep` to wait for processes
- Never mock modules you own; mock behaviours at the system edge
- Unique data per test (`System.unique_integer([:positive])`), so `async: true` stays safe
