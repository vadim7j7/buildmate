# Lookbook Patterns

Lookbook is a UI framework for ViewComponent (and Phlex) previews. It mounts at
`/lookbook` in development and provides a browseable component library, props
playground, and source viewer.

## Setup

```ruby
# Gemfile
group :development do
  gem 'lookbook'
end
```

```ruby
# config/routes.rb
Rails.application.routes.draw do
  if Rails.env.development?
    mount Lookbook::Engine, at: "/lookbook"
  end
end
```

```ruby
# config/application.rb
config.view_component.preview_paths << Rails.root.join("spec/components/previews")
config.view_component.default_preview_layout = "component_preview"
```

```erb
<!-- app/views/layouts/component_preview.html.erb -->
<!DOCTYPE html>
<html>
  <head>
    <%= csrf_meta_tags %>
    <%= csp_meta_tag %>
    <%= stylesheet_link_tag "application" %>
  </head>
  <body class="bg-white p-8">
    <%= yield %>
  </body>
</html>
```

## Preview Class

```ruby
# spec/components/previews/profile_card_component_preview.rb
# frozen_string_literal: true

class ProfileCardComponentPreview < ViewComponent::Preview
  # @!group Default

  def default
    profile = sample_profile
    render(ProfileCardComponent.new(profile:))
  end

  # @!endgroup

  # @!group Sizes

  # @param size [Symbol] select [sm, md, lg]
  def with_size(size: :md)
    render(ProfileCardComponent.new(profile: sample_profile, size: size.to_sym))
  end

  def small
    render(ProfileCardComponent.new(profile: sample_profile, size: :sm))
  end

  def medium
    render(ProfileCardComponent.new(profile: sample_profile, size: :md))
  end

  def large
    render(ProfileCardComponent.new(profile: sample_profile, size: :lg))
  end

  # @!endgroup

  # @!group Edge cases

  def with_long_bio
    profile = sample_profile
    profile.bio = 'A very long bio. ' * 30
    render(ProfileCardComponent.new(profile:))
  end

  def without_bio
    profile = sample_profile
    profile.bio = nil
    render(ProfileCardComponent.new(profile:))
  end

  # @!endgroup

  private

  def sample_profile
    Profile.new(
      name: 'Ada Lovelace',
      headline: 'Mathematician and writer',
      bio: 'Considered the first computer programmer.',
      avatar_url: 'https://placehold.co/80x80'
    )
  end
end
```

## Param Annotations

Lookbook reads YARD-style annotations to render interactive controls:

```ruby
# @param label [String] text
def with_label(label: "Click me")
  render(ButtonComponent.new(label:))
end

# @param size [Symbol] select [sm, md, lg]
def with_size(size: :md)
  render(ButtonComponent.new(label: "Save", size: size.to_sym))
end

# @param dark [Boolean] toggle
def with_dark_mode(dark: false)
  content_tag(:div, class: dark ? "dark bg-gray-900 p-8" : "bg-white p-8") do
    render(ButtonComponent.new(label: "Save"))
  end
end

# @param count [Number] number
def with_count(count: 5)
  render(BadgeComponent.new(count:))
end
```

Supported control types: `text`, `textarea`, `select`, `toggle`, `number`,
`color`, `range`.

## Notes & Documentation

```ruby
# @notes A profile card with avatar, name, headline, and optional bio.
#        Use `size: :sm` for sidebar contexts and `size: :lg` for hero placements.
class ProfileCardComponentPreview < ViewComponent::Preview
  # @notes The default rendering. Use this as the starting point for design reviews.
  def default
    # ...
  end
end
```

## Pages (Markdown docs)

Lookbook supports Markdown pages alongside previews:

```
spec/components/previews/pages/00-getting-started.md.erb
spec/components/previews/pages/01-design-tokens.md.erb
```

Use them for design system docs, color palettes, spacing scales, and typography.

## Embeds

Embed a preview in a Markdown page:

```erb
<%= embed ProfileCardComponentPreview, :default %>
```

## Tags

Filter / group previews:

```ruby
class ProfileCardComponentPreview < ViewComponent::Preview
  # @label Profile card
  # @hidden_tags experimental, deprecated
  # @display max_width "600px"
  # @display bg_color "#f9fafb"

  def default
    # ...
  end
end
```

## Display Options

Control the preview iframe's appearance:

```ruby
# Class-level defaults
class ButtonComponentPreview < ViewComponent::Preview
  # @display max_width 400
  # @display bg_color "#f3f4f6"
end

# Per-example overrides
# @display max_width 800
# @display bg_color "#1f2937"   for dark backgrounds
def with_dark_background
  # ...
end
```

## Style Rules

1. **One preview class per component** — `<Name>ComponentPreview`
2. **Place in `spec/components/previews/`** (Rails default)
3. **Provide a `default` example** — designers expect it
4. **Group with `@!group` and `@!endgroup`** — Sizes, States, Edge cases
5. **Cover edge cases** — empty state, long content, missing optional fields, error state
6. **Use `Model.new(...)`** — never `create` (no DB pollution)
7. **Use sample data, not real users** — placeholders only
8. **Annotate `@param` for interactive playgrounds** — designers love these
9. **Add `@notes`** — explain when to use the component
10. **Pages for design tokens** — palette, spacing, typography in Markdown

## Common Pitfalls

| Symptom | Likely cause |
|---------|--------------|
| Lookbook shows "Preview not found" | Preview file not in `preview_paths`, or class name mismatch |
| Layout is broken | `default_preview_layout` not configured, or layout file missing |
| Tailwind classes don't apply | `tailwind.config.js` `content` doesn't include preview path |
| Page errors with `Rails.application.routes` | Mount inside `if Rails.env.development?` block |
| Real DB rows show up | Using `create` — switch to `new` or `build_stubbed` |
