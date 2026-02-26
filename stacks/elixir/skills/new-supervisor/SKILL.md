---
name: new-supervisor
description: Generate a Supervisor with child specs and restart strategy
---

# /new-supervisor

## What This Does

Generates a Supervisor module with child specifications and a test file.

## Usage

```
/new-supervisor MyApp.Workers.Supervisor      # Creates a worker supervisor
/new-supervisor MyApp.Pipeline.Supervisor     # Creates a pipeline supervisor
```

## How It Works

1. **Read reference patterns** from `patterns/backend-patterns.md`.
2. **Determine module name** and file path.
3. **Generate Supervisor** with:
   - `use Supervisor`
   - `start_link/1`
   - `init/1` with child specs and strategy
   - `@moduledoc` documentation
4. **Generate test file** verifying supervision tree starts correctly.
5. **Run quality checks**: `mix format`, `mix credo --strict`, `mix test`.

## Generated Files

```
lib/my_app/<path>/<module>.ex
test/my_app/<path>/<module>_test.exs
```
