# ViewComponent Style Guide

Conventions for naming, structuring, and writing ViewComponents.

## File Layout

```
app/components/
├── application_component.rb              # Base class
├── profile_card_component.rb             # Component class
├── profile_card_component.html.erb       # Sidecar template
└── profile_card_component_spec.rb        # (or in spec/components/)
```

Sidecar templates live next to the Ruby file so they move together.

## Naming

| Element | Convention | Example |
|---------|------------|---------|
| Class | `<Name>Component`, PascalCase | `ProfileCardComponent` |
| File | `<name>_component.rb`, snake_case | `profile_card_component.rb` |
| Template | `<name>_component.html.erb` | `profile_card_component.html.erb` |
| Preview | `<Name>ComponentPreview` | `ProfileCardComponentPreview` |
| Spec | `<name>_component_spec.rb` | `profile_card_component_spec.rb` |

The `Component` suffix is required by Rails autoloading.

## Class Structure (canonical order)

```ruby
# frozen_string_literal: true

# Class-level YARD docs explaining the component's purpose and usage.
#
# @example
#   render(ProfileCardComponent.new(profile: @profile, size: :md))
class ProfileCardComponent < ApplicationComponent
  # 1. Constants
  SIZES = %i[sm md lg].freeze
  VARIANTS = %i[default highlighted].freeze

  # 2. Slots (renders_one / renders_many)
  renders_one :header
  renders_many :actions

  # 3. initialize
  def initialize(profile:, size: :md, variant: :default)
    raise ArgumentError, "Invalid size: #{size}" unless SIZES.include?(size)

    @profile = profile
    @size = size
    @variant = variant
  end

  # 4. Public methods (read by template)
  # (Usually none — keep template-facing data in private attr_readers)

  private

  # 5. Private attr_reader
  attr_reader :profile, :size, :variant

  # 6. Private helpers (class composition, computed values)
  def container_classes
    base = 'rounded-lg border border-gray-200 bg-white p-4'
    size_class = SIZE_CLASSES.fetch(size)
    "#{base} #{size_class}"
  end

  SIZE_CLASSES = {
    sm: 'w-48',
    md: 'w-64',
    lg: 'w-full max-w-md'
  }.freeze
end
```

## initialize Conventions

- **Keyword arguments only** — never positional
- **Required args** have no default
- **Optional args** have a sensible default
- **Validate enum-like params** with constant lookups (raise `ArgumentError`)
- **Pass loaded data** — never IDs that the component would have to look up

```ruby
# BAD - DB query inside the component
def initialize(profile_id:)
  @profile = Profile.find(profile_id)
end

# GOOD - data is passed in
def initialize(profile:)
  @profile = profile
end
```

## Template Conventions

- One sidecar template per component (`<name>_component.html.erb`)
- Use `t('...')` for ALL user-visible strings
- Use semantic HTML: `<article>`, `<header>`, `<nav>`, `<section>`
- Compose Tailwind classes via private methods on the component
- Reference data via private `attr_reader` (defined on the component)

```erb
<article class="<%= container_classes %>" aria-labelledby="profile-<%= profile.id %>">
  <header class="flex items-center gap-3">
    <%= image_tag profile.avatar_url,
                  class: "w-10 h-10 rounded-full",
                  alt: profile.name %>
    <div>
      <h3 id="profile-<%= profile.id %>" class="font-semibold"><%= profile.name %></h3>
      <p class="text-sm text-gray-500"><%= profile.headline %></p>
    </div>
  </header>

  <% if profile.bio.present? %>
    <p class="mt-3 text-sm text-gray-700"><%= profile.bio %></p>
  <% end %>
</article>
```

## Inline `call` Method (no sidecar)

For tiny components (<5 lines of HTML), define `call` instead:

```ruby
class StatusBadgeComponent < ApplicationComponent
  def initialize(status:)
    @status = status
  end

  def call
    classes = case @status.to_s
              when 'active'   then 'bg-green-100 text-green-800'
              when 'archived' then 'bg-red-100 text-red-800'
              else                 'bg-gray-100 text-gray-800'
              end
    tag.span(@status.to_s.titleize,
             class: "inline-flex px-2 py-0.5 rounded text-xs #{classes}")
  end
end
```

Above ~5 lines of HTML, switch to a sidecar template.

## Slots

```ruby
class CardComponent < ApplicationComponent
  renders_one :header
  renders_one :footer
  renders_many :actions, "ActionButton"
end
```

Use `renders_one` for at-most-one slot, `renders_many` for collections. Pass a
class name (string) or block to specify the slot's component.

```erb
<article>
  <% if header? %>
    <header><%= header %></header>
  <% end %>

  <%= content %>

  <% if actions? %>
    <footer>
      <% actions.each { |a| %>
        <%= a %>
      <% } %>
    </footer>
  <% end %>
</article>
```

## Constants and Lookups

Prefer `freeze`-d constants for enum-like values and class lookups:

```ruby
SIZES = %i[sm md lg].freeze

SIZE_CLASSES = {
  sm: 'w-48',
  md: 'w-64',
  lg: 'w-full max-w-md'
}.freeze
```

Validate input against the enum:

```ruby
raise ArgumentError, "Invalid size: #{size}" unless SIZES.include?(size)
```

## Internationalization

ALL user-visible strings go through `t('...')`:

```erb
<button><%= t('common.save') %></button>
<p><%= t('profiles.empty_state.message') %></p>
```

Never hardcode English. Even "Save", "Cancel", "Delete" — they need translation.

## Accessibility

- **Always provide `alt` text** on images
- **Always pair labels with form fields** (visible or `sr-only`)
- **Use semantic HTML** — `<article>`, `<header>`, `<nav>`, `<section>`, `<main>`
- **Use ARIA only when semantic HTML isn't enough** — don't paste ARIA on everything
- **Keep heading order semantic** — h1 → h2 → h3, no skipping
- **Provide focus indicators** — `focus:ring-2 focus:ring-blue-500` etc.

## Performance

- **NO database queries inside the component** — pass loaded data in
- **Use `with_collection` for list rendering** — built-in optimization
- **Avoid creating ActiveRecord objects** in private methods if avoidable
- **Cache expensive components** with `cache @component_args do ... end` if rendering is slow

## Style Rules (mandatory)

1. **`frozen_string_literal: true`** on every component file
2. **Inherit from `ApplicationComponent`**
3. **Class name ends in `Component`**
4. **File name in snake_case**: `profile_card_component.rb`
5. **Sidecar template** for non-trivial markup; inline `call` for tiny ones
6. **Keyword args** in `initialize`
7. **Private `attr_reader`** for instance variables
8. **NO database queries** inside the component
9. **Validate enum-like params** with constants
10. **Compose CSS via private methods** — never inline string concatenation
11. **`t('...')` for all strings**
12. **YARD docs** on `initialize`
13. **Always have a spec**
14. **Always have a Lookbook preview** when Lookbook is enabled
