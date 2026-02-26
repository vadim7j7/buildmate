---
name: new-context
description: Generate a Phoenix context with schema, changeset, and tests
---

# /new-context

## What This Does

Generates a Phoenix context module with an Ecto schema, changeset, CRUD functions,
and corresponding tests.

## Usage

```
/new-context Accounts User     # Creates Accounts context with User schema
/new-context Blog Post          # Creates Blog context with Post schema
/new-context Catalog Product    # Creates Catalog context with Product schema
```

## How It Works

1. **Read reference patterns** from `patterns/phoenix-patterns.md` and `patterns/backend-patterns.md`.
2. **Determine context and schema names** from arguments.
3. **Generate Ecto schema** with changeset, typespecs, and query functions.
4. **Generate context module** with CRUD functions (`list_`, `get_`, `create_`, `update_`, `delete_`).
5. **Generate migration** for the database table.
6. **Generate test file** with ConnCase tests for each CRUD operation.
7. **Run quality checks**: `mix format`, `mix credo --strict`, `mix test`.

## Generated Files

```
lib/my_app/<context>.ex
lib/my_app/<context>/<schema>.ex
priv/repo/migrations/<timestamp>_create_<table>.exs
test/my_app/<context>_test.exs
```
