# TailwindCSS in Rails Patterns

This file covers how to use TailwindCSS effectively in a Rails monolith with
ViewComponents and Hotwire.

## Setup (tailwindcss-rails 4.x, Tailwind v4)

```bash
bundle add tailwindcss-rails
bin/rails tailwindcss:install
```

This uses the standalone Tailwind binary (`tailwindcss-ruby`): **no Node, no
`package.json`, no `tailwind.config.js`**. It adds:
- `app/assets/tailwind/application.css` (the input file, starts with `@import "tailwindcss";`)
- `app/assets/builds/tailwind.css` (build output, git-ignored, served by Propshaft)
- `Procfile.dev` entry: `css: bin/rails tailwindcss:watch`

Build once with `bin/rails tailwindcss:build`; `assets:precompile` runs it in
production. An app still on v3 (`tailwind.config.js`, `application.tailwind.css`)
migrates with `bin/rails tailwindcss:upgrade`; check the diff before committing.

## Configuration Lives in CSS

```css
/* app/assets/tailwind/application.css */
@import "tailwindcss";

/* First-party plugins ship inside the standalone binary */
@plugin "@tailwindcss/forms";
@plugin "@tailwindcss/typography";

/* Design tokens: each variable becomes utilities (bg-brand-500, text-brand-900) */
@theme {
  --color-brand-50: #eff6ff;
  --color-brand-500: #3b82f6;
  --color-brand-900: #1e3a8a;
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
}

/* Only for files automatic detection misses (e.g. templates inside a gem) */
@source "../../../vendor/engines/admin/app";
```

**Source detection**: v4 scans the project automatically (it skips files in
`.gitignore` and binary files), so `app/views`, `app/components`, `app/helpers`
and `app/javascript` are covered without listing them. Add `@source` only for
paths outside the app or ignored by git.

## Class Composition Patterns

### Pattern 1: Inline (simple, used once)

```erb
<button class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
  Save
</button>
```

OK when the button appears in just one place.

### Pattern 2: Helper method (reusable, presentation-only)

```ruby
# app/helpers/buttons_helper.rb
module ButtonsHelper
  def primary_button_classes
    'px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50'
  end

  def secondary_button_classes
    'px-4 py-2 border border-gray-300 rounded hover:bg-gray-50'
  end
end
```

```erb
<%= form.submit class: primary_button_classes %>
<%= link_to 'Cancel', :back, class: secondary_button_classes %>
```

### Pattern 3: ViewComponent (variants, logic)

```ruby
# app/components/button_component.rb
class ButtonComponent < ApplicationComponent
  VARIANTS = %i[primary secondary danger].freeze
  SIZES = %i[sm md lg].freeze

  def initialize(label:, url: nil, variant: :primary, size: :md, type: :button, **html_options)
    @label = label
    @url = url
    @variant = variant
    @size = size
    @type = type
    @html_options = html_options
  end

  def call
    classes = [base_classes, variant_classes, size_classes].join(' ')

    if @url
      link_to @label, @url, class: classes, **@html_options
    else
      button_tag @label, type: @type, class: classes, **@html_options
    end
  end

  private

  def base_classes
    'inline-flex items-center justify-center font-medium rounded transition-colors disabled:opacity-50'
  end

  def variant_classes
    case @variant
    when :primary   then 'bg-blue-600 text-white hover:bg-blue-700'
    when :secondary then 'border border-gray-300 hover:bg-gray-50'
    when :danger    then 'bg-red-600 text-white hover:bg-red-700'
    end
  end

  def size_classes
    case @size
    when :sm then 'px-3 py-1 text-sm'
    when :md then 'px-4 py-2 text-base'
    when :lg then 'px-6 py-3 text-lg'
    end
  end
end
```

Usage:

```erb
<%= render(ButtonComponent.new(label: 'Save', type: :submit, variant: :primary)) %>
<%= render(ButtonComponent.new(label: 'Delete', url: profile_path(@profile),
                                variant: :danger, size: :sm,
                                data: { turbo_method: :delete })) %>
```

## Class Ordering Convention

Group classes by category for readability:

```
layout → spacing → sizing → typography → color → border → effect → state
```

Example:

```html
<!-- BAD: random order -->
<div class="hover:bg-gray-50 px-4 mt-2 text-sm rounded border bg-white py-2 flex items-center">

<!-- GOOD: grouped -->
<div class="flex items-center px-4 py-2 mt-2 text-sm bg-white border rounded hover:bg-gray-50">
```

Tools like `prettier-plugin-tailwindcss` can auto-sort classes — consider adopting.

## Responsive Variants

Mobile-first: base classes apply to all sizes; prefix with `sm:`, `md:`, `lg:`,
`xl:`, `2xl:` to override at breakpoints.

```html
<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
```

## State Variants

```html
<button class="bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 disabled:opacity-50">
```

`hover:`, `focus:`, `focus-visible:`, `active:`, `disabled:`, `aria-expanded:`,
`data-[state=open]:`, etc.

## Dark Mode

v4 follows `prefers-color-scheme` by default. For a manual toggle, redefine the
variant in `application.css`:

```css
@custom-variant dark (&:where(.dark, .dark *));
```

Then use `dark:` variant:

```html
<div class="bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
```

Toggle via a Stimulus controller that adds/removes `class="dark"` on `<html>`.

## Forms Plugin

`@tailwindcss/forms` resets browser form styling so Tailwind classes work
predictably (enable it with `@plugin "@tailwindcss/forms";`):

```html
<input type="text" class="rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" />
```

## Common Patterns

### Card

```html
<article class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
  <h3 class="font-semibold">...</h3>
  <p class="mt-2 text-sm text-gray-600">...</p>
</article>
```

### Page wrapper

```html
<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  ...
</main>
```

### Sticky header

```html
<header class="sticky top-0 z-10 bg-white border-b">
  ...
</header>
```

## Style Rules

1. **Group classes** — layout → spacing → sizing → typography → color → border → effect → state
2. **Extract repeated patterns** — into a helper or ViewComponent after 3+ uses
3. **Mobile-first responsive** — base classes are mobile, override with breakpoint prefixes
4. **Use design tokens** — define brand colors / spacing in `@theme` in `app/assets/tailwind/application.css`, not as raw hex throughout
5. **Don't fight Tailwind with `@apply`** — extract to a component instead
6. **No `tailwind.config.js`** — configuration is CSS-first (`@theme`, `@plugin`, `@source`, `@custom-variant`); don't add Node tooling for Tailwind
7. **Always provide `alt` text and labels** — utility classes don't fix accessibility issues

## Common Pitfalls

| Symptom | Likely cause |
|---------|--------------|
| Class doesn't apply | File is git-ignored or outside the app: add an `@source` line; or `tailwindcss:watch` isn't running (use `bin/dev`) |
| Class string built dynamically doesn't apply | Tailwind can't see strings constructed at runtime — list possible classes statically |
| Dark mode flash on load | Toggle script runs after CSS — set the class before page render via inline `<script>` |
| Forms look unstyled | Missing `@plugin "@tailwindcss/forms";` |
| Old v3 classes look wrong (`shadow-sm`, `rounded`, `ring`) | v4 renamed the scale (`shadow-xs`, `rounded-sm`, `ring-3`): run `bin/rails tailwindcss:upgrade` |

### Dynamic class construction caveat

```ruby
# BAD - Tailwind can't see "bg-blue-600" because it's built at runtime
def container_class(color)
  "bg-#{color}-600"
end

# GOOD - all possible class strings are visible to Tailwind
def container_class(color)
  case color
  when :blue   then 'bg-blue-600'
  when :green  then 'bg-green-600'
  when :red    then 'bg-red-600'
  end
end
```

The Tailwind compiler scans source files; strings interpolated at runtime aren't
visible during the build. Always use literal class strings (or
`@source inline("bg-red-600 bg-green-600");` for truly dynamic classes).
