---
name: new-controller
description: Generate a Phoenix controller with actions and tests
---

# /new-controller

## What This Does

Generates a Phoenix JSON API controller with CRUD actions, JSON view, and
ConnCase tests.

## Usage

```
/new-controller Post           # Creates PostController with CRUD actions
/new-controller User           # Creates UserController with CRUD actions
```

## How It Works

1. **Read reference patterns** from `patterns/phoenix-patterns.md`.
2. **Determine controller name** and resource from argument.
3. **Generate controller** with:
   - `use MyAppWeb, :controller`
   - `action_fallback MyAppWeb.FallbackController`
   - CRUD actions: index, show, create, update, delete
   - `with` expressions for error handling
4. **Generate JSON view** with render functions.
5. **Generate ConnCase test** for each action.
6. **Add resource route** to router.
7. **Run quality checks**: `mix format`, `mix credo --strict`, `mix test`.

## Generated Files

```
lib/my_app_web/controllers/<resource>_controller.ex
lib/my_app_web/controllers/<resource>_json.ex
test/my_app_web/controllers/<resource>_controller_test.exs
```
