---
name: new-partial
description: Generate an ERB partial with an explicit locals contract
---

# /new-partial

## What This Does

Creates a new ERB partial in `app/views/<resource>/_<name>.html.erb`. Documents
the partial's `locals:` contract at the top of the file so callers know what
to pass.

## Usage

```
/new-partial profiles form
/new-partial shared header
/new-partial layouts flash_messages
```

## How It Works

### 1. Read Patterns

- `styles/erb-style.md`
- Existing partials in `app/views/` for project conventions

### 2. Determine Locals Contract

What does the caller need to provide? Document this at the top of the partial.

### 3. Generate the Partial

#### Form partial: `app/views/profiles/_form.html.erb`

```erb
<%#
  locals:
    profile: Profile     - the model instance (new or persisted)
    submit_label: String - optional, defaults to translated default
%>

<% submit_label ||= profile.persisted? ? t('common.update') : t('common.create') %>

<%= form_with(model: profile, class: "space-y-4") do |form| %>
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
    <%= form.label :name, class: "block text-sm font-medium text-gray-700" %>
    <%= form.text_field :name,
                        required: true,
                        class: "mt-1 block w-full rounded border-gray-300 shadow-sm" %>
  </div>

  <div>
    <%= form.label :email, class: "block text-sm font-medium text-gray-700" %>
    <%= form.email_field :email,
                          class: "mt-1 block w-full rounded border-gray-300 shadow-sm" %>
  </div>

  <div class="flex justify-end gap-2">
    <%= link_to t('common.cancel'), :back, class: "px-4 py-2 border rounded" %>
    <%= form.submit submit_label, class: "px-4 py-2 bg-blue-600 text-white rounded" %>
  </div>
<% end %>
```

Caller (with explicit `locals:`):

```erb
<%= render "form", profile: @profile %>
<%= render "form", profile: @profile, submit_label: t('profiles.update') %>
```

#### Shared partial: `app/views/shared/_header.html.erb`

```erb
<%#
  locals:
    user: User - the signed-in user (must be present)
%>

<header class="bg-white border-b">
  <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
    <%= link_to root_path, class: "font-bold text-lg" do %>
      <%= t('app.name') %>
    <% end %>

    <nav class="flex items-center gap-4">
      <%= link_to t('navigation.profiles'), profiles_path %>
      <%= button_to t('navigation.sign_out'), destroy_user_session_path,
                    method: :delete,
                    data: { turbo_confirm: t('common.confirm_sign_out') } %>
    </nav>
  </div>
</header>
```

### 4. Verify

The template syntax is checked at render time. To verify quickly:

```bash
bin/rails runner 'puts ApplicationController.render(template: "profiles/index", assigns: { profiles: [] })'
# Or run a system spec that exercises the view
```

## Rules

- Document the `locals:` contract at the top using `<%# %>` comments
- Always pass locals **explicitly**: `render "form", profile: @profile`
- NEVER rely on instance variables (`@profile`) in a partial — break encapsulation
- If a partial needs >3 locals, consider promoting it to a ViewComponent
- Use `t('...')` for all strings
- Provide ARIA roles on dynamic alerts/status regions
- Default optional locals at the top of the partial

## Partial vs ViewComponent — When to choose

Choose a partial when:
- The markup is mostly static
- Used only in 1–2 places
- No conditional class logic

Choose a ViewComponent when:
- 3+ usages
- Variants (size, color, state)
- Computed class names
- Slots needed (header / body / footer)
- You want a unit-testable rendering

## Output

```
Created:
  app/views/profiles/_form.html.erb

Locals contract:
  - profile: Profile
  - submit_label: String (optional)

Caller example:
  <%= render "form", profile: @profile %>
```
