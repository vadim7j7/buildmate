---
name: new-component
description: Create a HEEx function component with declared attrs and slots, plus a test
---

# /new-component

## What This Does

Creates a stateless function component (`Phoenix.Component`) with `attr` and `slot`
declarations, in the project's components module, and a render test. Use a
LiveComponent only when the piece needs its own state and events (`/new-live`).

## Usage

```
/new-component badge                  # small reusable piece in core_components.ex
/new-component Blog.post_card         # domain component in MyAppWeb.BlogComponents
```

## How It Works

1. **Read** `lib/my_app_web/components/core_components.ex` first: it may already have
   the component (button, input, table, modal, flash, icon), and new components should
   follow its style (CSS approach, `class` merging, `@rest`).
2. **Pick the module**: generic UI goes in `CoreComponents`; domain components in a
   module such as `MyAppWeb.BlogComponents` (`use Phoenix.Component`), imported where used
   or added to the `html_helpers` in `my_app_web.ex`.
3. **Write the component**:

```elixir
@doc """
Renders a status badge.

## Examples

    <.badge status={:published} />
    <.badge status={:draft} class="ml-2">Draft</.badge>
"""
attr :status, :atom, required: true, values: [:draft, :published, :archived]
attr :class, :any, default: nil
attr :rest, :global

slot :inner_block

def badge(assigns) do
  ~H"""
  <span class={["badge", badge_class(@status), @class]} {@rest}>
    {render_slot(@inner_block) || Phoenix.Naming.humanize(@status)}
  </span>
  """
end

defp badge_class(:draft), do: "badge-ghost"
defp badge_class(:published), do: "badge-success"
defp badge_class(:archived), do: "badge-neutral"
```

   Named slots with attributes, for structured content:

```elixir
slot :item, required: true do
  attr :title, :string, required: true
end

def card_list(assigns) do
  ~H"""
  <ul>
    <li :for={item <- @item}>
      <h3>{item.title}</h3>
      {render_slot(item)}
    </li>
  </ul>
  """
end
```

4. **Test** it with `rendered_to_string/1` (`import Phoenix.LiveViewTest`):

```elixir
test "badge falls back to the status name" do
  assigns = %{}
  html = rendered_to_string(~H"<.badge status={:draft} />")
  assert html =~ "Draft"
end
```

5. **Run** `mix format`, `mix compile --warnings-as-errors` (catches missing required
   attrs and unknown `values:` at compile time), `mix test`.

## Rules

- Declare every attr and slot; `required: true` where the component cannot work without it
- `attr :rest, :global` to pass through HTML attributes (`id`, `phx-click`, `data-*`)
- Function components are pure: no Repo calls, no `send`; the caller passes data in
- HEEx escapes output; never `raw/1` with user content
- Use `{@value}` interpolation in bodies and attributes; `<%= %>` only inside blocks
  where the project already does
