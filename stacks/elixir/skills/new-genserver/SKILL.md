---
name: new-genserver
description: Generate a GenServer with handle_call/cast/info, init, and test
---

# /new-genserver

## What This Does

Generates a GenServer module with client API, server callbacks, and a test file.

## Usage

```
/new-genserver MyApp.Cache             # Creates a cache GenServer
/new-genserver MyApp.Workers.Poller    # Creates a polling worker
```

## How It Works

1. **Read reference patterns** from `patterns/backend-patterns.md`.
2. **Determine module name** and file path.
3. **Generate GenServer** with:
   - `use GenServer`
   - `start_link/1` with keyword options
   - Client API functions
   - `@impl true` on all callbacks: `init/1`, `handle_call/3`, `handle_cast/2`
   - `@doc` and `@spec` on all public functions
4. **Generate test file** using `start_supervised!` for process lifecycle.
5. **Run quality checks**: `mix format`, `mix credo --strict`, `mix test`.

## Generated Files

```
lib/my_app/<path>/<module>.ex
test/my_app/<path>/<module>_test.exs
```
