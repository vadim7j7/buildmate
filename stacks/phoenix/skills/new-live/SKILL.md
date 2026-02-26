---
name: new-live
description: Generate a Phoenix LiveView with mount, events, and test
---

# /new-live

## What This Does

Generates a Phoenix LiveView module with mount, handle_event, render, and a
corresponding LiveView test file.

## Usage

```
/new-live PostLive.Index       # Creates index LiveView for posts
/new-live UserLive.Show        # Creates show LiveView for users
/new-live DashboardLive        # Creates a dashboard LiveView
```

## How It Works

1. **Read reference patterns** from `patterns/phoenix-patterns.md`.
2. **Determine LiveView module name** and file path.
3. **Generate LiveView** with:
   - `use MyAppWeb, :live_view`
   - `mount/3`, `handle_params/3`, `handle_event/3` with `@impl true`
   - `render/1` with HEEx template
   - Streams for list views
4. **Generate test file** using `LiveViewTest`.
5. **Add route** to router if applicable.
6. **Run quality checks**: `mix format`, `mix credo --strict`, `mix test`.

## Generated Files

```
lib/my_app_web/live/<live_view>.ex
test/my_app_web/live/<live_view>_test.exs
```
