---
name: new-helper
description: Generate a Rails view helper module for purely presentational logic
---

# /new-helper

## What This Does

Creates a Rails view helper module in `app/helpers/`. Helpers expose formatting,
class-name, and HTML-building methods to views and ViewComponents. They contain
**presentation-only** logic — no DB queries, no business rules.

## Usage

```
/new-helper Profiles
/new-helper Navigation
/new-helper Formatting
```

## How It Works

### 1. Read Patterns

- `patterns/rails-monolith-patterns.md`
- `styles/erb-style.md`
- Existing helpers in `app/helpers/`

### 2. Generate the Helper Module

`app/helpers/profiles_helper.rb`:

```ruby
# frozen_string_literal: true

# Presentation helpers for Profile views and components.
#
# Helpers are STATELESS and PRESENTATION-ONLY. No DB queries. No business logic.
module ProfilesHelper
  # @param status [String, Symbol]
  # @return [String] CSS classes for the badge
  def profile_status_classes(status)
    base = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium'
    color = case status.to_s
            when 'active'   then 'bg-green-100 text-green-800'
            when 'inactive' then 'bg-gray-100 text-gray-800'
            when 'archived' then 'bg-red-100 text-red-800'
            else                 'bg-gray-100 text-gray-800'
            end
    "#{base} #{color}"
  end

  # @param profile [Profile]
  # @return [ActiveSupport::SafeBuffer] avatar HTML
  def profile_avatar(profile, size: :md)
    dimensions = case size
                 when :sm then 'w-6 h-6'
                 when :md then 'w-10 h-10'
                 when :lg then 'w-16 h-16'
                 end

    image_tag profile.avatar_url(size: size),
              class: "#{dimensions} rounded-full",
              alt: profile.name
  end

  # @param time [Time, nil]
  # @return [String] human-readable relative time
  def relative_time(time)
    return '' if time.nil?

    "#{time_ago_in_words(time)} #{t('common.ago')}"
  end
end
```

### 3. Generate the Spec

`spec/helpers/profiles_helper_spec.rb`:

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe ProfilesHelper do
  describe '#profile_status_classes' do
    it 'returns green classes for active' do
      expect(helper.profile_status_classes('active')).to include('bg-green-100', 'text-green-800')
    end

    it 'returns gray classes for unknown statuses' do
      expect(helper.profile_status_classes('unknown')).to include('bg-gray-100')
    end
  end

  describe '#profile_avatar' do
    let(:profile) { build_stubbed(:profile, name: 'Ada') }

    it 'renders an image tag with alt text' do
      result = helper.profile_avatar(profile)
      expect(result).to include('alt="Ada"')
      expect(result).to include('rounded-full')
    end
  end
end
```

### 4. Run Quality Checks

```bash
bundle exec rubocop -A app/helpers/<name>_helper.rb spec/helpers/<name>_helper_spec.rb
bundle exec rspec spec/helpers/<name>_helper_spec.rb
```

## Rules

- Helpers are PRESENTATION ONLY:
  - Format dates, currency, status labels
  - Compute CSS class strings from values
  - Build small bits of HTML with `tag.div`, `image_tag`, etc.
- NO database queries (no `Profile.find`, `current_user.profiles`, etc.)
- NO business logic — that belongs in models, services, or presenters
- ALWAYS YARD-document parameters and return types
- Use `t('...')` for any user-visible strings
- For complex computed HTML, prefer a ViewComponent over a helper

## When NOT to Add a Helper

If a method requires:
- A DB query → put it on the model or in a service
- Conditional rendering of large HTML blocks → ViewComponent
- Knowledge of `current_user` and authorization → ViewComponent or controller

## Output

```
Created:
  app/helpers/profiles_helper.rb
  spec/helpers/profiles_helper_spec.rb

Verified:
  bundle exec rubocop  -- PASS
  bundle exec rspec    -- PASS (X examples, 0 failures)
```
