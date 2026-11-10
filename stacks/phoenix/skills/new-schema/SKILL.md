---
name: new-schema
description: Create an Ecto schema with changesets, migration and tests inside a context
---

# /new-schema

## What This Does

Adds an Ecto schema to a context: the schema module with typed fields and
associations, one changeset per use case, its migration, and changeset tests.

## Usage

```
/new-schema Blog.Post posts title:string body:text status:enum user_id:references:users
/new-schema Billing.Invoice invoices number:string amount:decimal due_on:date
```

## How It Works

1. **Read** `.claude/patterns/phoenix-patterns.md` (Context, Schema), `auth.md`
   (scopes) and an existing schema in the same context. Match key type
   (`@primary_key {:id, :binary_id, autogenerate: true}`?) and timestamp type.
2. **Generate or write**:
   - Schema + migration only: `mix phx.gen.schema Blog.Post posts title:string body:text`
     (with a default scope configured it adds the owner field, e.g. `user_id`)
   - Schema + context functions + tests: `mix phx.gen.context Blog Post posts ...`
   - Review generated code; it is a starting point, not finished work
3. **Schema module**:

```elixir
defmodule MyApp.Blog.Post do
  use Ecto.Schema
  import Ecto.Changeset

  schema "posts" do
    field :title, :string
    field :body, :string
    field :status, Ecto.Enum, values: [:draft, :published], default: :draft
    belongs_to :user, MyApp.Accounts.User

    timestamps(type: :utc_datetime)
  end

  @doc "Changeset for user-editable fields. The owner comes from the scope, never params."
  def changeset(post, attrs, scope) do
    post
    |> cast(attrs, [:title, :body, :status])
    |> validate_required([:title])
    |> validate_length(:title, max: 200)
    |> unique_constraint([:user_id, :title])
    |> put_change(:user_id, scope.user.id)
  end
end
```

4. **Changeset rules**: `cast/4` lists only fields a user may set; separate changesets
   for different use cases (`registration_changeset`, `admin_changeset`); every DB
   constraint has its changeset counterpart (`unique_constraint`, `foreign_key_constraint`,
   `check_constraint`) so violations become errors, not exceptions. Money is `:decimal`.
5. **Migration**: as in `/new-migration` (indexes on foreign keys, `null: false` where
   required). Run `mix ecto.migrate`.
6. **Tests** (`test/my_app/blog/post_test.exs` or in the context test, `DataCase`):
   valid attrs, each required field, length/format limits, the unique constraint via
   `Repo.insert`, and that `user_id` in params is ignored.
7. **Run** `mix format`, `mix compile --warnings-as-errors`, `mix test`.

## Rules

- The schema is used only inside its context; other contexts call the context API
- Associations across contexts: reference by id (`field :user_id`) or `belongs_to`, but
  never call another context's Repo queries
- `Ecto.Enum` for fixed sets of values; never `String.to_atom` on input
- No business logic in the schema beyond changesets and small pure helpers
