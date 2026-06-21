# Stimulus Style Guide

Conventions for naming, structuring, and writing Stimulus controllers in a Rails
monolith.

## File Layout

```
app/javascript/controllers/
├── application.js                    # Stimulus app instance
├── index.js                          # Controller registration (eager_load_controllers if used)
├── dropdown_controller.js
├── auto_dismiss_controller.js
├── infinite_scroll_controller.js
└── modal_controller.js
```

## Naming

| Element | Convention | Example |
|---------|------------|---------|
| Filename | `<name>_controller.js` (snake_case) | `dropdown_controller.js` |
| Identifier (data-controller) | `<name>` (kebab-case) | `data-controller="dropdown"` |
| Multi-word filename | snake_case | `infinite_scroll_controller.js` |
| Multi-word identifier | kebab-case | `data-controller="infinite-scroll"` |
| Action method | camelCase, single responsibility | `toggleMenu`, `dismissAlert`, `loadMore` |
| Target | camelCase, noun | `menu`, `submitButton`, `placeholder` |
| Value | camelCase, noun | `open`, `count`, `delay` |

## Controller Skeleton

```js
import { Controller } from "@hotwired/stimulus"

// Brief description of what this controller does and the HTML structure
// it expects. Document the data attributes a caller must provide.
//
// data-controller="dropdown" data-dropdown-open-value="false"
// Targets: trigger, menu
// Values:  open (Boolean)
// Classes: hidden
export default class extends Controller {
  static targets = ["trigger", "menu"]
  static values  = { open: Boolean }
  static classes = ["hidden"]

  connect() {
    this.update()
  }

  toggle(event) {
    event.preventDefault()
    this.openValue = !this.openValue
  }

  openValueChanged() {
    this.update()
  }

  update() {
    this.menuTarget.classList.toggle(this.hiddenClass, !this.openValue)
    this.triggerTarget.setAttribute("aria-expanded", String(this.openValue))
  }
}
```

## Static API Members (canonical order)

Always declare static members in this order:

```js
static targets = []
static values  = {}
static classes = []
static outlets = []
```

## Lifecycle Order

```js
initialize() { /* once, before any connect */ }
connect()    { /* each attach to DOM */ }
disconnect() { /* each detach from DOM */ }
```

If you add window/document listeners in `connect()`, ALWAYS remove them in
`disconnect()`:

```js
connect() {
  this.boundResize = this.handleResize.bind(this)
  window.addEventListener("resize", this.boundResize)
}

disconnect() {
  window.removeEventListener("resize", this.boundResize)
}
```

## Reading the DOM

NEVER use `document.querySelector` inside a controller. Use targets:

```js
// BAD
this.element.querySelector(".menu").classList.toggle("hidden")

// GOOD
this.menuTarget.classList.toggle(this.hiddenClass)
```

If a target might not exist, check first:

```js
if (this.hasSummaryTarget) {
  this.summaryTarget.textContent = "Updated"
}
```

## Reactive Updates

Prefer `<value>Changed` callbacks over imperative DOM updates:

```js
// AVOID - imperative
toggle() {
  this.openValue = !this.openValue
  this.menuTarget.classList.toggle(this.hiddenClass, !this.openValue)
  this.triggerTarget.setAttribute("aria-expanded", this.openValue)
}

// PREFER - reactive
toggle() {
  this.openValue = !this.openValue
}

openValueChanged() {
  this.menuTarget.classList.toggle(this.hiddenClass, !this.openValue)
  this.triggerTarget.setAttribute("aria-expanded", String(this.openValue))
}
```

This makes the controller idempotent — calling `openValueChanged()` from
`connect()` ensures the DOM matches state on initial load.

## Action Naming

Action methods describe what the user does, not what the DOM does:

| Good | Avoid |
|------|-------|
| `submit` | `handleClick` |
| `loadMore` | `onScroll` |
| `dismiss` | `removeNode` |
| `copyToClipboard` | `clickHandler` |

## Event Specifiers

```html
<!-- Default: click for buttons, submit for forms, change for inputs -->
<button data-action="dropdown#toggle">

<!-- Explicit event -->
<input data-action="input->autosave#save">

<!-- Multiple events on same element -->
<form data-action="submit->autosave#submit input->autosave#save">

<!-- Window/document scope -->
<div data-controller="modal"
     data-action="keydown@window->modal#closeOnEscape">
```

## Values

Use the typed values API:

```js
static values = {
  count: Number,
  open: Boolean,
  url: String,
  items: Array,
  config: Object,
  delay: { type: Number, default: 300 }   // with default
}
```

```html
<div data-controller="counter"
     data-counter-count-value="0"
     data-counter-url-value="/increment">
```

## Outlets

Use outlets for cross-controller communication:

```js
static outlets = ["modal"]

open() {
  this.modalOutlet.show()
}

modalOutletConnected(controller, element) {
  // Called when the modal outlet attaches
}
```

```html
<aside data-controller="sidebar" data-sidebar-modal-outlet="#confirm-modal">
  <button data-action="sidebar#open">Open</button>
</aside>

<dialog id="confirm-modal" data-controller="modal">...</dialog>
```

## Don'ts

- **Don't query the DOM** — use targets / outlets
- **Don't store state in the DOM** — use values
- **Don't write inline event handlers** — use `data-action`
- **Don't use jQuery** — vanilla DOM is fine, Stimulus handles delegation
- **Don't share state between controllers via globals** — use outlets or events
- **Don't skip `disconnect()` cleanup** — Turbo navigation reattaches controllers, so leaks compound

## Keep Controllers Small

If a controller exceeds ~80 lines, consider:
- Splitting into multiple controllers (one per responsibility)
- Moving complex logic to a separate ES module
- Asking whether the feature should be server-rendered (Turbo Frame/Stream) instead

## Style Rules

1. **One responsibility per controller**
2. **Static members in canonical order**: `targets` → `values` → `classes` → `outlets`
3. **Clean up listeners** in `disconnect()` if added in `connect()`
4. **Use `<value>Changed` callbacks** for reactive updates
5. **NO `document.querySelector`** — use `this.<name>Target`
6. **NO inline event handlers** — use `data-action`
7. **NO global state** — values + outlets only
8. **Filename matches identifier**: `dropdown` ↔ `dropdown_controller.js`
9. **Multi-word names**: kebab in HTML, snake in filename
10. **Document the HTML contract** at the top of the controller (data attributes, targets, classes)
11. **Prefer Turbo over Stimulus** for server-driven UI

## Common Pitfalls

| Symptom | Likely cause |
|---------|--------------|
| Controller doesn't activate | Filename / data-controller mismatch, or import path wrong |
| `Cannot read property 'classList' of undefined` | Target name typo, or target missing in HTML |
| Memory leak after Turbo navigation | Forgot `disconnect()` cleanup |
| Value doesn't propagate to DOM | Define a `<name>ValueChanged` callback or update DOM imperatively |
| `this` is wrong inside callback | Use arrow function OR bind in constructor/connect |
| Action fires for the wrong element | Use `event.currentTarget` (the element with the action) vs `event.target` (where the event originated) |

## Testing

Stimulus controllers are tested via system specs (Capybara `js: true`). The
view-tester agent owns these. Don't write JS unit tests — system tests verify
real browser behavior, which is what matters.
