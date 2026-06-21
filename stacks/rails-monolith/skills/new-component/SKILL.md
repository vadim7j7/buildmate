---
name: new-component
description: Generate a ViewComponent with sidecar template, spec, and (optional) Lookbook preview
---

# /new-component

## What This Does

Creates a new ViewComponent following project conventions: a Ruby class in
`app/components/`, a sidecar ERB template, an RSpec component spec, and (when
Lookbook is enabled) a preview class.

## Usage

```
/new-component ProfileCard
/new-component AlertBanner
/new-component AnswerCard
/new-component ConfirmDialog
```

## How It Works

### 1. Analyze Requirements

Determine from the component name + context:
- What props (initialize parameters) does it need?
- Does it have variants (size, color, state)?
- Does it need slots (header / body / footer)?
- Does it need TailwindCSS class composition logic?

### 2. Read Existing Patterns

Before generating, read:
- `patterns/view-component-patterns.md`
- `styles/view-component-style.md`
- `styles/erb-style.md`
- Existing components in `app/components/` for project-specific conventions

### 3. Generate Files

#### Component class: `app/components/<name>_component.rb`

```ruby
# frozen_string_literal: true

# Renders a profile card with avatar, name, headline, and optional bio.
#
# @example
#   render(ProfileCardComponent.new(profile: @profile, size: :md))
class ProfileCardComponent < ApplicationComponent
  SIZES = %i[sm md lg].freeze

  # @param profile [Profile]
  # @param size [Symbol] one of SIZES
  def initialize(profile:, size: :md)
    raise ArgumentError, "Invalid size: #{size}" unless SIZES.include?(size)

    @profile = profile
    @size = size
  end

  private

  attr_reader :profile, :size

  def container_classes
    base = 'rounded-lg border border-gray-200 bg-white p-4'
    width = case size
            when :sm then 'w-48'
            when :md then 'w-64'
            when :lg then 'w-full max-w-md'
            end
    "#{base} #{width}"
  end
end
```

#### Sidecar template: `app/components/<name>_component.html.erb`

```erb
<article class="<%= container_classes %>">
  <header class="flex items-center gap-3">
    <%= image_tag profile.avatar_url, class: "w-10 h-10 rounded-full", alt: profile.name %>
    <div>
      <h3 class="font-semibold"><%= profile.name %></h3>
      <p class="text-sm text-gray-500"><%= profile.headline %></p>
    </div>
  </header>

  <% if profile.bio.present? %>
    <p class="mt-3 text-sm text-gray-700"><%= profile.bio %></p>
  <% end %>
</article>
```

#### Spec: `spec/components/<name>_component_spec.rb`

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe ProfileCardComponent, type: :component do
  let(:profile) { build_stubbed(:profile, name: 'Ada Lovelace', headline: 'Engineer') }

  it 'renders the profile name' do
    render_inline(described_class.new(profile:))

    expect(page).to have_css('h3', text: 'Ada Lovelace')
  end

  describe 'size variants' do
    it 'applies w-48 for :sm' do
      render_inline(described_class.new(profile:, size: :sm))
      expect(page).to have_css('article.w-48')
    end

    it 'raises on invalid size' do
      expect { described_class.new(profile:, size: :xxl) }
        .to raise_error(ArgumentError, /Invalid size/)
    end
  end
end
```

#### Lookbook preview (when `--preview=lookbook`): `spec/components/previews/<name>_component_preview.rb`

```ruby
# frozen_string_literal: true

class ProfileCardComponentPreview < ViewComponent::Preview
  def default
    profile = Profile.new(name: 'Ada Lovelace', headline: 'Engineer', bio: 'Sample bio.')
    render(ProfileCardComponent.new(profile:))
  end

  def small
    profile = Profile.new(name: 'Ada Lovelace', headline: 'Engineer')
    render(ProfileCardComponent.new(profile:, size: :sm))
  end

  def large_with_long_bio
    profile = Profile.new(
      name: 'Ada Lovelace',
      headline: 'Engineer',
      bio: 'A long bio to test wrapping. ' * 10
    )
    render(ProfileCardComponent.new(profile:, size: :lg))
  end
end
```

### 4. Verify

Run:

```bash
bundle exec rubocop -A app/components/<name>_component.rb spec/components/<name>_component_spec.rb
bundle exec rspec spec/components/<name>_component_spec.rb
```

## Rules

- Inherit from `ApplicationComponent`
- Use **keyword arguments** in `initialize`
- Use **private `attr_reader`** for instance variables
- **NO database queries** inside the component — pass data in
- Sidecar template lives next to the `.rb` file (`<name>_component.html.erb`)
- Use `t('...')` for any user-visible strings
- Validate enum-like params (sizes, colors) with a `SIZES = %i[...].freeze` constant
- Compose Tailwind classes via private methods (`container_classes`, `button_classes`)
- Component name ends in `Component` (Rails convention)

## Component vs Partial

Use a ViewComponent when:
- The same UI appears in 3+ places
- There's non-trivial computation (class names, conditional structure)
- The component has variants
- You want unit-testable rendering

Use a partial when:
- Rendered once or twice
- Simple, mostly-static markup
- No variants

## Output

```
Created:
  app/components/profile_card_component.rb
  app/components/profile_card_component.html.erb
  spec/components/profile_card_component_spec.rb
  spec/components/previews/profile_card_component_preview.rb  (if Lookbook enabled)

Verified:
  bundle exec rubocop  -- PASS
  bundle exec rspec    -- PASS (X examples, 0 failures)
```
