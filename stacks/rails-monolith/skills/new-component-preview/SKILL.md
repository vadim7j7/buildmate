---
name: new-component-preview
description: Generate a Lookbook preview class for an existing ViewComponent
---

# /new-component-preview

## What This Does

Creates a Lookbook preview class in `spec/components/previews/` so designers and
developers can browse, configure, and visually test a ViewComponent in isolation.

This skill is enabled when `--preview=lookbook`.

## Usage

```
/new-component-preview ProfileCard
/new-component-preview AlertBanner
/new-component-preview ConfirmDialog
```

## How It Works

### 1. Verify the Component Exists

```bash
test -f app/components/<name>_component.rb || echo "Component not found"
```

If not, suggest running `/new-component` first.

### 2. Read the Component

Open `app/components/<name>_component.rb` to determine:
- What `initialize` parameters it accepts
- What variants exist (sizes, colors, states)

### 3. Generate the Preview

`spec/components/previews/profile_card_component_preview.rb`:

```ruby
# frozen_string_literal: true

# Lookbook preview for ProfileCardComponent.
#
# @display bg_color "#f9fafb"
class ProfileCardComponentPreview < ViewComponent::Preview
  # @!group Default

  # Default rendering with a sample profile.
  def default
    profile = sample_profile
    render(ProfileCardComponent.new(profile:))
  end

  # @!endgroup

  # @!group Sizes

  # @param size [Symbol] select [sm, md, lg]
  def with_size(size: :md)
    profile = sample_profile
    render(ProfileCardComponent.new(profile:, size: size.to_sym))
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

  # Profile with a long bio to test wrapping and truncation.
  def with_long_bio
    profile = sample_profile
    profile.bio = 'A long bio to test how text wraps within the card. ' * 10
    render(ProfileCardComponent.new(profile:))
  end

  # Profile with no bio (empty state).
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

### 4. Verify

```bash
bin/rails server
# Visit http://localhost:3000/lookbook
# Navigate to ProfileCardComponentPreview
```

Run the component spec to ensure preview data still works:

```bash
bundle exec rspec spec/components/profile_card_component_spec.rb
```

## Rules

- Place in `spec/components/previews/<name>_component_preview.rb` (Rails default)
- Class name: `<Name>ComponentPreview` inheriting from `ViewComponent::Preview`
- Provide a `default` example, then variant scenarios
- Use `@!group` and `@!endgroup` to organize by category (Sizes, States, Edge cases)
- Use `@param` annotations for interactive controls (Lookbook's "params" panel)
- Use `Model.new(...)` (not `create`) so previews don't pollute the DB
- Cover **edge cases**: empty state, long content, missing optional fields
- Never use real user data in previews — use placeholders or generic samples

## Lookbook Param Annotations

```ruby
# @param size [Symbol] select [sm, md, lg]
def with_size(size: :md)
  # ...
end

# @param dark [Boolean] toggle
def with_dark_mode(dark: false)
  # ...
end

# @param label [String] text
def with_custom_label(label: "Click me")
  # ...
end
```

## Output

```
Created:
  spec/components/previews/profile_card_component_preview.rb

Preview at:
  http://localhost:3000/lookbook → ProfileCardComponentPreview

Examples included:
  - default
  - small / medium / large (size variants)
  - with_long_bio (wrapping)
  - without_bio (empty state)
```
