# ERB Style Guide

Conventions for ERB templates (views, partials, mailer templates) in a Rails
monolith.

## File Layout

```
app/views/
├── layouts/
│   ├── application.html.erb
│   └── mailer.html.erb
├── shared/
│   ├── _flash.html.erb
│   └── _header.html.erb
├── profiles/
│   ├── index.html.erb
│   ├── show.html.erb
│   ├── new.html.erb
│   ├── edit.html.erb
│   └── _form.html.erb
└── user_mailer/
    ├── welcome.html.erb
    └── welcome.text.erb
```

## Naming

- Views are named after the controller action: `index.html.erb`, `show.html.erb`
- Partials start with `_`: `_form.html.erb`, `_flash.html.erb`
- Format extension before engine: `index.html.erb`, NOT `index.erb.html`
- Turbo Stream views: `<action>.turbo_stream.erb`
- Mailer templates: HTML (`.html.erb`) AND text (`.text.erb`) versions

## Strings

ALL user-visible strings go through `t('...')`:

```erb
<%# BAD %>
<h1>Profile</h1>
<button>Save</button>

<%# GOOD %>
<h1><%= t('profiles.show.title') %></h1>
<button><%= t('common.save') %></button>
```

Even single words ("Save", "Cancel", "Edit") need translation keys.

## Tag Helpers

For non-trivial HTML, prefer `tag.<name>` over manual string interpolation:

```erb
<%# GOOD %>
<%= tag.div class: 'rounded p-3', role: 'alert' do %>
  <%= message %>
<% end %>

<%# AVOID - manual string building is error-prone for HTML %>
<%= "<div class='rounded p-3'>#{message}</div>".html_safe %>
```

## Loops & Conditionals

Use one-liner `<% %>` for control flow, with `<%= %>` for output:

```erb
<% if @profiles.any? %>
  <ul>
    <% @profiles.each do |profile| %>
      <li><%= profile.name %></li>
    <% end %>
  </ul>
<% else %>
  <p><%= t('profiles.empty') %></p>
<% end %>
```

Avoid logic-heavy templates — extract to:
- A helper (for formatting / class names)
- A ViewComponent (for reusable UI)
- A presenter (for data shaping)

## Partials

Always pass locals **explicitly**:

```erb
<%# BAD - relies on instance variable %>
<%= render "form" %>

<%# GOOD - explicit locals %>
<%= render "form", profile: @profile %>
```

NEVER access instance variables (`@profile`) inside a partial — it breaks
encapsulation. Always pass via locals.

Document the locals contract at the top of the partial:

```erb
<%# locals:
      profile: Profile
      submit_label: String (optional)
%>

<% submit_label ||= profile.persisted? ? t('common.update') : t('common.create') %>
...
```

## Links and Buttons

| Use | Helper | When |
|-----|--------|------|
| Navigation | `link_to` | GET to a URL |
| State change (POST/PATCH/DELETE) | `button_to` | Form-submit-style action |
| Form submit | `form.submit` | Inside a `form_with` |

```erb
<%= link_to t('common.edit'), edit_profile_path(@profile),
            class: "text-blue-600 hover:underline" %>

<%= button_to t('common.destroy'), profile_path(@profile),
              method: :delete,
              data: { turbo_confirm: t('common.confirm_destroy') },
              class: "px-3 py-1 text-red-600" %>
```

`button_to` generates a real form with CSRF token and proper HTTP method.
Don't fake state changes via `link_to` with `data-method`.

## Forms

Use `form_with`:

```erb
<%= form_with(model: @profile) do |form| %>
  <%= form.label :name %>
  <%= form.text_field :name, required: true %>
  <%= form.submit %>
<% end %>
```

NEVER use `form_for` (deprecated) or `form_tag` (low-level, no model integration).

## Turbo Frames

```erb
<%= turbo_frame_tag "profile_#{@profile.id}" do %>
  ...
<% end %>
```

Frame IDs must be unique on the page. Use stable, descriptive IDs.

## Layouts

```erb
<!DOCTYPE html>
<html lang="<%= I18n.locale %>" class="h-full">
  <head>
    <title><%= content_for(:title) || t('app.name') %></title>
    <%= csrf_meta_tags %>
    <%= csp_meta_tag %>
    <%= stylesheet_link_tag "application", "data-turbo-track": "reload" %>
    <%= javascript_importmap_tags %>
  </head>
  <body class="h-full bg-gray-50">
    <%= render "shared/header" %>
    <%= render "shared/flash" %>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <%= yield %>
    </main>
  </body>
</html>
```

Use `content_for :title` in views to set the page title:

```erb
<% content_for :title, @profile.name %>
```

## Comments

```erb
<%# This is a server-side comment, not rendered to the page. %>

<%#
  Multi-line server-side comment.
  Use for documenting locals, behavior notes, etc.
%>
```

Don't use HTML comments (`<!-- ... -->`) for server-side notes — they leak to
the rendered page. Use `<%# %>`.

## Whitespace

Use the `-` modifiers to trim whitespace in compact loops:

```erb
<%# Without trim - extra blank lines in output %>
<% items.each do |item| %>
  <%= item %>
<% end %>

<%# With trim %>
<% items.each do |item| -%>
  <%= item %>
<% end -%>
```

Most projects don't bother — Rails' default ERB output is fine for HTML where
whitespace doesn't matter. Use trim only when generating whitespace-sensitive
output (text emails, generated source files).

## Accessibility

- **Images need `alt`** — always
- **Form fields need labels** — visible or `sr-only`
- **Use semantic HTML** — `<article>`, `<header>`, `<nav>`, `<section>`, `<main>`
- **Heading order is semantic** — `<h1>` once per page, then `<h2>` → `<h3>`
- **Interactive elements are keyboard-accessible** — buttons not divs with onclick
- **Color contrast meets WCAG AA**

## Style Rules

1. **`t('...')` for all user-visible strings** — no exceptions
2. **Pass locals explicitly to partials** — never rely on `@instance_variable`
3. **Document locals contract** at the top of partials
4. **Use `link_to` for GET, `button_to` for state changes**
5. **Use `form_with`** — never `form_for` or `form_tag`
6. **Semantic HTML** — `<article>`, `<header>`, `<nav>`, `<section>`, `<main>`
7. **`<%# %>` for comments** — not HTML comments
8. **Format ext before engine** — `index.html.erb`, not `index.erb.html`
9. **Always provide `alt` and form labels** — accessibility
10. **Extract logic to helpers, components, or presenters** — keep templates dumb

## Common Pitfalls

| Symptom | Likely cause |
|---------|--------------|
| `undefined method` in partial | Used `@profile` instead of local `profile` |
| Translations missing in production | Forgot to add keys to `config/locales/*.yml` |
| HTML comments showing in source | Used `<!-- -->` instead of `<%# %>` |
| CSRF errors on form submit | Layout missing `csrf_meta_tags` |
| Turbo confirm doesn't work | `data: { turbo_confirm: ... }` instead of `data: { confirm: ... }` (legacy) |
| Form submit doesn't refresh | Form is inside a frame but the response doesn't have a matching frame |
