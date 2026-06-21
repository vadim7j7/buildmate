# ViewComponent Patterns

ViewComponents are Ruby classes that render HTML. They encapsulate reusable UI
with testable logic and explicit interfaces. Use them when the same UI repeats
across views, when there's non-trivial class composition, or when variants exist.

## ApplicationComponent Base

Every component inherits from `ApplicationComponent`. This base class lives at
`app/components/application_component.rb`:

```ruby
# frozen_string_literal: true

class ApplicationComponent < ViewComponent::Base
  include ApplicationHelper
  # Add cross-component helpers here (e.g. icon helpers, design tokens)
end
```

## Basic Component (sidecar template)

`app/components/profile_card_component.rb`:

```ruby
# frozen_string_literal: true

# Renders a profile card with avatar, name, and optional bio.
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

`app/components/profile_card_component.html.erb`:

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

## Slots (Composition)

When a component has structured regions (header / body / footer, or a list of items):

```ruby
# frozen_string_literal: true

class CardComponent < ApplicationComponent
  renders_one :header
  renders_one :footer
  renders_many :actions, "ActionButton"

  class ActionButton < ApplicationComponent
    def initialize(label:, url:, variant: :default)
      @label = label
      @url = url
      @variant = variant
    end

    def call
      classes = case @variant
                when :primary then 'bg-blue-600 text-white'
                else                'bg-gray-100 text-gray-900'
                end
      link_to @label, @url, class: "px-3 py-1 rounded #{classes}"
    end
  end
end
```

Template:

```erb
<article class="rounded-lg border bg-white">
  <% if header? %>
    <header class="border-b p-3"><%= header %></header>
  <% end %>

  <div class="p-4"><%= content %></div>

  <% if actions? %>
    <footer class="border-t p-3 flex gap-2">
      <% actions.each { |a| %>
        <%= a %>
      <% } %>
    </footer>
  <% end %>
</article>
```

Caller:

```erb
<%= render(CardComponent.new) do |card| %>
  <% card.with_header { tag.h2('Profile') } %>
  <p>Card body content here.</p>
  <% card.with_action(label: 'Edit',   url: edit_profile_path, variant: :primary) %>
  <% card.with_action(label: 'Delete', url: profile_path, variant: :default) %>
<% end %>
```

## Collections (`with_collection`)

When rendering a list of the same component:

```erb
<%= render(ProfileCardComponent.with_collection(@profiles, size: :md)) %>
```

Each profile becomes `profile:` in the component (Rails convention: collection
parameter inferred from class name; override with `with_collection_parameter`).

## Inline Templates (`call` method)

For tiny components without significant markup, define `call` instead of a sidecar:

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
    tag.span(@status.to_s.titleize, class: "inline-flex px-2 py-0.5 rounded text-xs #{classes}")
  end
end
```

## Spec Pattern

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe ProfileCardComponent, type: :component do
  let(:profile) { build_stubbed(:profile, name: 'Ada Lovelace', headline: 'Engineer') }

  it 'renders the name' do
    render_inline(described_class.new(profile:))
    expect(page).to have_css('h3', text: 'Ada Lovelace')
  end

  it 'omits bio when blank' do
    profile.bio = nil
    render_inline(described_class.new(profile:))
    expect(page).not_to have_css('p.text-gray-700')
  end

  describe 'size variants' do
    it 'applies w-48 for :sm' do
      render_inline(described_class.new(profile:, size: :sm))
      expect(page).to have_css('article.w-48')
    end
  end
end
```

Use `build_stubbed` over `create` when no DB is needed — much faster.

## Lookbook Preview

```ruby
class ProfileCardComponentPreview < ViewComponent::Preview
  def default
    profile = Profile.new(name: 'Ada Lovelace', headline: 'Engineer', bio: 'Sample.')
    render(ProfileCardComponent.new(profile:))
  end

  # @param size [Symbol] select [sm, md, lg]
  def with_size(size: :md)
    profile = Profile.new(name: 'Ada Lovelace', headline: 'Engineer')
    render(ProfileCardComponent.new(profile:, size: size.to_sym))
  end
end
```

## Rules

1. **Inherit from `ApplicationComponent`**
2. **Keyword args** in `initialize`
3. **Private `attr_reader`** for instance variables
4. **NO database queries** inside the component — pass data in
5. **Sidecar template** (`<name>_component.html.erb`) for components with non-trivial markup
6. **Inline `call` method** for tiny components (<5 lines of HTML)
7. **Validate enum-like params** with constants (`SIZES = %i[...].freeze`)
8. **Compose Tailwind classes** via private methods, not inline string concatenation
9. **Component name ends in `Component`** — Rails convention enforces this
10. **Use `t('...')`** for any user-visible strings
11. **Always have a spec** in `spec/components/`
12. **Provide a Lookbook preview** when Lookbook is enabled

## When to Use a Component

| Scenario | Component? |
|----------|------------|
| Same UI in 3+ places | Yes |
| Variants (size, color, state) | Yes |
| Computed class names | Yes |
| Slot composition (header/body/footer) | Yes |
| Used once, simple markup | No → partial |
| Logic depends on `current_user` / authorization | Reconsider — pass it in or use a helper |
