# Stimulus Patterns

Stimulus is a tiny JS framework that augments HTML with behavior. Controllers
attach to elements via `data-controller`, expose `data-action` event handlers,
read/write DOM via `targets`, and manage state via `values`.

You write the JS in `app/javascript/controllers/`. With `stimulus-rails` and
`importmap-rails` (or `jsbundling-rails`), controllers are auto-registered.

## Anatomy

```js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["menu", "trigger"]
  static values = { open: Boolean, url: String }
  static classes = ["hidden", "active"]
  static outlets = ["modal"]

  connect() {
    // Called when the controller attaches to the DOM
  }

  disconnect() {
    // Called when the controller detaches — clean up here
  }

  toggle(event) {
    event.preventDefault()
    this.openValue = !this.openValue
  }

  openValueChanged(open) {
    this.menuTarget.classList.toggle(this.hiddenClass, !open)
  }
}
```

Wired up in HTML:

```erb
<div data-controller="dropdown"
     data-dropdown-open-value="false"
     data-dropdown-hidden-class="hidden">
  <button data-dropdown-target="trigger"
          data-action="dropdown#toggle">
    Options
  </button>
  <ul data-dropdown-target="menu" class="hidden">
    <li><%= link_to 'Edit', edit_path %></li>
  </ul>
</div>
```

## Targets

Targets are DOM references. Declare with `static targets = [...]`, access via
`this.<name>Target` (single) or `this.<name>Targets` (array).

```js
static targets = ["item", "summary"]

clear() {
  this.itemTargets.forEach(el => el.remove())
  this.summaryTarget.textContent = "0 items"
}
```

Check existence with `this.has<Name>Target`:

```js
if (this.hasSummaryTarget) {
  this.summaryTarget.textContent = "Updated"
}
```

## Values

Values are typed state. Declare with `static values = { name: Type }`. Setting
`this.<name>Value` automatically calls `<name>ValueChanged(newValue, oldValue)`
if defined.

```js
static values = { count: Number, open: Boolean, url: String, items: Array }

increment() {
  this.countValue += 1   // triggers countValueChanged
}

countValueChanged(value) {
  this.element.querySelector("output").textContent = value
}
```

Wire up via data attributes:

```erb
<div data-controller="counter"
     data-counter-count-value="0"
     data-counter-url-value="<%= increment_path %>">
  ...
</div>
```

## Classes

CSS class names from data attributes (avoid hardcoding utility classes in JS):

```js
static classes = ["hidden", "active"]

show() {
  this.element.classList.remove(this.hiddenClass)
  this.element.classList.add(this.activeClass)
}
```

```erb
<div data-controller="modal"
     data-modal-hidden-class="hidden"
     data-modal-active-class="ring-2 ring-blue-500">
  ...
</div>
```

## Actions

```erb
<!-- Click on this element -->
<button data-action="dropdown#toggle">Toggle</button>

<!-- Specific event -->
<input data-action="input->autosave#save">

<!-- Multiple events -->
<form data-action="submit->autosave#submit input->autosave#save">

<!-- Window-level events -->
<div data-controller="modal"
     data-action="keydown@window->modal#closeOnEscape click@window->modal#closeOnOutside">
```

## Outlets (controller-to-controller communication)

```js
// app/javascript/controllers/sidebar_controller.js
static outlets = ["modal"]

open() {
  this.modalOutlet.show()  // calls show() on the connected modal controller
}
```

```erb
<aside data-controller="sidebar" data-sidebar-modal-outlet="#confirm-modal">
  <button data-action="sidebar#open">Open modal</button>
</aside>

<dialog id="confirm-modal" data-controller="modal">...</dialog>
```

## Lifecycle

```js
export default class extends Controller {
  initialize() {
    // Once per controller instance
  }

  connect() {
    // Each time the controller attaches to the DOM (Turbo navigation re-attaches)
    this.boundResize = this.handleResize.bind(this)
    window.addEventListener("resize", this.boundResize)
  }

  disconnect() {
    // Clean up listeners added in connect()
    window.removeEventListener("resize", this.boundResize)
  }

  handleResize(event) {
    // ...
  }
}
```

## Common Patterns

### Auto-submit form on input change

```js
// app/javascript/controllers/autosubmit_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = { delay: { type: Number, default: 300 } }

  submit() {
    clearTimeout(this.timeout)
    this.timeout = setTimeout(() => this.element.requestSubmit(), this.delayValue)
  }
}
```

```erb
<%= form_with(url: search_path, method: :get,
              data: { controller: "autosubmit", autosubmit_delay_value: 300 }) do |form| %>
  <%= form.text_field :query, data: { action: "input->autosubmit#submit" } %>
<% end %>
```

### Copy to clipboard

```js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["source", "feedback"]

  async copy() {
    await navigator.clipboard.writeText(this.sourceTarget.value)
    this.feedbackTarget.textContent = "Copied!"
    setTimeout(() => { this.feedbackTarget.textContent = "" }, 2000)
  }
}
```

### Confirm before action

For destructive buttons, prefer Turbo's built-in `data-turbo-confirm`:

```erb
<%= button_to t('common.delete'), profile_path(@profile),
              method: :delete,
              data: { turbo_confirm: t('common.confirm_destroy') } %>
```

Only write a Stimulus controller for this if you need custom UI (a modal, not a
native `confirm()`).

### Reveal on scroll / IntersectionObserver

```js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static classes = ["visible"]

  connect() {
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add(...this.visibleClasses)
        }
      })
    })
    this.observer.observe(this.element)
  }

  disconnect() {
    this.observer.disconnect()
  }
}
```

## Rules

1. **One controller per responsibility** — small, focused, named after what they do
2. **Use static `targets`, `values`, `classes`, `outlets`** — never query the DOM via `document.querySelector`
3. **Use `*Changed` callbacks** for reactive updates, not imperative DOM manipulation
4. **Clean up listeners in `disconnect()`** if added in `connect()`
5. **No global state** — all state goes on `static values`
6. **No inline event handlers** — always use `data-action`
7. **Filename matches data-controller name**: `dropdown` → `dropdown_controller.js`
8. **Multi-word names** use kebab-case in HTML, snake_case in filename: `infinite-scroll` → `infinite_scroll_controller.js`
9. **Prefer Turbo over Stimulus** for server-driven UI — only reach for Stimulus when you genuinely need client-side state

## Common Pitfalls

| Symptom | Likely cause |
|---------|--------------|
| Controller doesn't attach | Filename / data-controller mismatch, or import path wrong |
| Target is undefined | `static targets` missing the name, or `data-<ctrl>-target` typo |
| `this.element` is wrong | Action delegated from a window event — use `event.currentTarget` |
| Memory leak / duplicate listeners | Forgot `disconnect()` cleanup; Turbo navigation reattaches |
| Value not updating in DOM | Define a `<name>ValueChanged` callback or update DOM imperatively |

## Testing

Stimulus behavior is tested via system specs (Capybara with `js: true`). See
`patterns/forms-patterns.md` and the `view-tester` agent for examples.
