---
name: new-module
description: Generate an Elixir module with typespec and documentation
---

# /new-module

## What This Does

Generates an Elixir module with `@moduledoc`, `@doc`, `@spec`, and a corresponding
test file.

## Usage

```
/new-module MyApp.Users.UserService    # Creates lib/my_app/users/user_service.ex
/new-module MyApp.Notifications        # Creates lib/my_app/notifications.ex
```

## How It Works

1. **Read reference patterns** from `patterns/backend-patterns.md` and `styles/backend-elixir.md`.
2. **Determine module name** and file path from the argument.
3. **Generate module** with `@moduledoc`, public functions with `@doc` and `@spec`.
4. **Generate test file** with ExUnit `describe` blocks.
5. **Run quality checks**: `mix format`, `mix credo --strict`, `mix test`.

## Generated Files

```
lib/my_app/<path>/<module>.ex
test/my_app/<path>/<module>_test.exs
```
