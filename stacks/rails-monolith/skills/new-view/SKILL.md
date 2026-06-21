---
name: new-view
description: Generate a new ERB view for an existing controller action with route check
---

# /new-view

## What This Does

Creates a new ERB view file for an existing controller action. Sets up the basic
layout, links to the controller's instance variables, and includes flash/error
boilerplate consistent with the project.

Use this when the controller already exists and you just need to add or replace
a view file.

## Usage

```
/new-view profiles index           # app/views/profiles/index.html.erb
/new-view admin/companies show     # app/views/admin/companies/show.html.erb
/new-view dashboard home           # app/views/dashboard/home.html.erb
```

## How It Works

### 1. Read Patterns

- `patterns/rails-monolith-patterns.md`
- `patterns/forms-patterns.md` (if generating new/edit)
- `styles/erb-style.md`

### 2. Verify the Controller and Action Exist

```bash
bin/rails routes | grep <resource>
```

If the route doesn't exist, suggest the route entry and stop.

### 3. Generate the View

#### `index.html.erb`

```erb
<% content_for :title, t('profiles.index.title') %>

<header class="mb-6 flex items-center justify-between">
  <h1 class="text-2xl font-bold"><%= t('profiles.index.title') %></h1>
  <%= link_to t('profiles.index.new'), new_profile_path,
              class: "px-4 py-2 bg-blue-600 text-white rounded" %>
</header>

<% if @profiles.any? %>
  <ul class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    <% @profiles.each do |profile| %>
      <li>
        <%= render(ProfileCardComponent.new(profile:)) %>
      </li>
    <% end %>
  </ul>

  <%== pagy_nav(@pagy) if defined?(@pagy) %>
<% else %>
  <p class="text-gray-500"><%= t('profiles.index.empty') %></p>
<% end %>
```

#### `show.html.erb`

```erb
<% content_for :title, @profile.name %>

<%= turbo_frame_tag "profile_#{@profile.id}" do %>
  <%= render(ProfileCardComponent.new(profile: @profile, size: :lg)) %>

  <div class="mt-4 flex gap-2">
    <%= link_to t('common.edit'), edit_profile_path(@profile),
                class: "px-3 py-1 border rounded" %>
    <%= button_to t('common.destroy'), profile_path(@profile),
                  method: :delete,
                  data: { turbo_confirm: t('common.confirm_destroy') },
                  class: "px-3 py-1 border rounded text-red-600" %>
  </div>
<% end %>
```

#### `new.html.erb` / `edit.html.erb`

```erb
<% content_for :title, t('profiles.new.title') %>

<h1 class="text-2xl font-bold mb-6"><%= t('profiles.new.title') %></h1>

<%= render "form", profile: @profile %>
```

(Pair this with the `_form.html.erb` partial — see `/new-partial` or `/new-form-component`.)

### 4. Suggest i18n Keys

Print the i18n keys to add to `config/locales/en.yml`:

```yaml
en:
  profiles:
    index:
      title: "Profiles"
      new: "New profile"
      empty: "No profiles yet."
    new:
      title: "New profile"
    create:
      success: "Profile created."
    update:
      success: "Profile updated."
    destroy:
      success: "Profile deleted."
```

### 5. Verify

```bash
# Render the page through a system spec or manually
bundle exec rails server
# Visit http://localhost:3000/profiles
```

## Rules

- Use `t('...')` for ALL user-visible strings — never hardcode English
- Use ViewComponents for repeated UI; partials only for layout-y composition
- Use `content_for :title, ...` to set `<title>` from the layout
- Use `link_to` for navigation, `button_to` for state-changing actions
- Wrap edit-able sections in `turbo_frame_tag` if inline editing is desired
- Use `data: { turbo_confirm: t('...') }` for destructive confirmations
- Use semantic HTML: `<header>`, `<article>`, `<nav>`, `<section>`, `<main>`
- Always provide `alt` on images and labels on form fields

## Output

```
Created:
  app/views/profiles/index.html.erb

Suggested i18n keys (config/locales/en.yml):
  en.profiles.index.title
  en.profiles.index.new
  en.profiles.index.empty

Verified:
  bin/rails routes | grep profiles  -- OK
```
