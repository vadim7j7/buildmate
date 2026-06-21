---
name: new-form-component
description: Generate a reusable form ViewComponent that wraps form_with with error rendering
---

# /new-form-component

## What This Does

Creates a ViewComponent that encapsulates a model-backed form. The component
renders `form_with` with consistent error display, field styling, and Turbo-aware
submit behavior.

Use this when the same form structure repeats across new/edit/inline-edit views
and you want a single source of truth.

## Usage

```
/new-form-component ProfileForm
/new-form-component CommentForm
/new-form-component CompanyForm
```

## How It Works

### 1. Read Patterns

- `patterns/forms-patterns.md`
- `patterns/view-component-patterns.md`
- `styles/view-component-style.md`

### 2. Generate the Form Component

`app/components/profile_form_component.rb`:

```ruby
# frozen_string_literal: true

# Renders the Profile form (used on new and edit views, and inside Turbo Frames).
#
# @example
#   render(ProfileFormComponent.new(profile: @profile))
#   render(ProfileFormComponent.new(profile: @profile, submit_label: t('profiles.save')))
class ProfileFormComponent < ApplicationComponent
  # @param profile [Profile]
  # @param submit_label [String, nil] override the default submit button label
  # @param url [String, nil] override the form action (for nested resources)
  def initialize(profile:, submit_label: nil, url: nil)
    @profile = profile
    @submit_label = submit_label
    @url = url
  end

  private

  attr_reader :profile, :url

  def submit_label
    @submit_label || (profile.persisted? ? t('common.update') : t('common.create'))
  end

  def field_classes
    'mt-1 block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
  end

  def label_classes
    'block text-sm font-medium text-gray-700'
  end

  def submit_classes
    'px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50'
  end
end
```

### 3. Generate the Sidecar Template

`app/components/profile_form_component.html.erb`:

```erb
<%= form_with(model: profile, url: url, class: "space-y-4") do |form| %>
  <% if profile.errors.any? %>
    <div role="alert" class="rounded bg-red-50 border border-red-200 p-3">
      <h2 class="font-semibold text-red-800">
        <%= t('errors.messages.validation_failed', count: profile.errors.count) %>
      </h2>
      <ul class="mt-2 list-disc list-inside text-sm text-red-700">
        <% profile.errors.full_messages.each do |msg| %>
          <li><%= msg %></li>
        <% end %>
      </ul>
    </div>
  <% end %>

  <div>
    <%= form.label :name, class: label_classes %>
    <%= form.text_field :name, required: true, class: field_classes %>
  </div>

  <div>
    <%= form.label :email, class: label_classes %>
    <%= form.email_field :email, class: field_classes %>
  </div>

  <div>
    <%= form.label :bio, class: label_classes %>
    <%= form.text_area :bio, rows: 4, class: field_classes %>
  </div>

  <div class="flex justify-end gap-2">
    <%= link_to t('common.cancel'), :back, class: "px-4 py-2 border rounded" %>
    <%= form.submit submit_label, class: submit_classes %>
  </div>
<% end %>
```

### 4. Generate the Spec

`spec/components/profile_form_component_spec.rb`:

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe ProfileFormComponent, type: :component do
  let(:profile) { build_stubbed(:profile, name: 'Ada') }

  it 'renders form fields' do
    render_inline(described_class.new(profile:))

    expect(page).to have_field('Name', with: 'Ada')
    expect(page).to have_field('Email')
    expect(page).to have_field('Bio')
  end

  it 'shows the create label for new records' do
    profile = build(:profile)
    render_inline(described_class.new(profile:))

    expect(page).to have_button(/create/i)
  end

  it 'shows the update label for persisted records' do
    render_inline(described_class.new(profile:))

    expect(page).to have_button(/update/i)
  end

  it 'renders validation errors' do
    profile.name = nil
    profile.valid?
    render_inline(described_class.new(profile:))

    expect(page).to have_text("Name can't be blank")
  end

  it 'allows custom submit label' do
    render_inline(described_class.new(profile:, submit_label: 'Save profile'))

    expect(page).to have_button('Save profile')
  end
end
```

### 5. Update Views to Use the Component

Replace existing `_form.html.erb` partials and direct `form_with` blocks with:

```erb
<%= render(ProfileFormComponent.new(profile: @profile)) %>
```

### 6. Verify

```bash
bundle exec rubocop -A app/components/<name>_form_component.{rb,html.erb}
bundle exec rspec spec/components/<name>_form_component_spec.rb
```

## Rules

- Use `form_with` (NOT `form_for` or `form_tag`) — Turbo defaults
- Render errors with `role="alert"` for accessibility
- Default submit label based on `persisted?`
- Allow `url:` override for nested resources
- Default field/label/submit class strings via private methods
- Always require keyword args in `initialize`
- The matching controller MUST render with `status: :unprocessable_entity` on validation failure or Turbo will not re-render the form

## Output

```
Created:
  app/components/profile_form_component.rb
  app/components/profile_form_component.html.erb
  spec/components/profile_form_component_spec.rb

Caller example:
  <%= render(ProfileFormComponent.new(profile: @profile)) %>

Verified:
  bundle exec rspec  -- PASS (5 examples, 0 failures)
```
