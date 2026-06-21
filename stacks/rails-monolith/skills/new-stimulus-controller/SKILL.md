---
name: new-stimulus-controller
description: Generate a Stimulus controller with targets, values, and a system spec
---

# /new-stimulus-controller

## What This Does

Creates a new Stimulus controller in `app/javascript/controllers/` with proper
target/value/class declarations, lifecycle hooks, and a Capybara system spec
that exercises the behavior in a headless browser.

## Usage

```
/new-stimulus-controller dropdown
/new-stimulus-controller copy-to-clipboard
/new-stimulus-controller infinite-scroll
```

## How It Works

### 1. Read Existing Patterns

Before generating, read:
- `patterns/stimulus-patterns.md`
- `styles/stimulus-style.md`
- Existing controllers in `app/javascript/controllers/` to match conventions

### 2. Determine Surface Area

From the controller name + context, decide:
- What **targets** are needed? (DOM elements the controller reads/writes)
- What **values** are needed? (state held on the controller)
- What **actions** are exposed? (event handlers)
- What **classes** are toggled? (CSS class names from data attributes)

### 3. Generate Files

#### Controller: `app/javascript/controllers/<name>_controller.js`

```js
import { Controller } from "@hotwired/stimulus"

// Toggles a dropdown menu open/closed.
// Closes on outside click and Escape.
//
// data-controller="dropdown" data-dropdown-open-value="false"
// data-action="click@window->dropdown#closeOnOutside keydown@window->dropdown#closeOnEscape"
export default class extends Controller {
  static targets = ["menu", "trigger"]
  static values = { open: Boolean }
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

  closeOnOutside(event) {
    if (this.element.contains(event.target)) return
    this.openValue = false
  }

  closeOnEscape(event) {
    if (event.key === "Escape") this.openValue = false
  }

  update() {
    this.menuTarget.classList.toggle(this.hiddenClass, !this.openValue)
    this.triggerTarget.setAttribute("aria-expanded", this.openValue)
  }
}
```

#### Registration: `app/javascript/controllers/index.js`

If the project uses `eager_load` on the controllers directory, registration is
automatic. Otherwise, append:

```js
import DropdownController from "./dropdown_controller"
application.register("dropdown", DropdownController)
```

#### System spec: `spec/system/dropdown_spec.rb`

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'Dropdown', type: :system, js: true do
  before do
    visit '/components_test/dropdown' # or the page that renders this control
  end

  it 'opens on click and closes on outside click' do
    expect(page).to have_css('[data-dropdown-target="menu"].hidden')

    click_button 'Options'
    expect(page).not_to have_css('[data-dropdown-target="menu"].hidden')

    find('body').click
    expect(page).to have_css('[data-dropdown-target="menu"].hidden')
  end

  it 'closes on Escape' do
    click_button 'Options'
    find('body').send_keys(:escape)

    expect(page).to have_css('[data-dropdown-target="menu"].hidden')
  end
end
```

### 4. Suggest HTML Wiring

Print the data-attributes the user needs to add to their view:

```erb
<div data-controller="dropdown"
     data-dropdown-open-value="false"
     data-dropdown-hidden-class="hidden"
     data-action="click@window->dropdown#closeOnOutside keydown@window->dropdown#closeOnEscape">
  <button data-dropdown-target="trigger"
          data-action="dropdown#toggle"
          aria-expanded="false">
    Options
  </button>
  <ul data-dropdown-target="menu" class="hidden">
    <li><%= link_to 'Edit', edit_path %></li>
  </ul>
</div>
```

### 5. Verify

```bash
# JS lint if configured
yarn run lint app/javascript/controllers/<name>_controller.js
# System spec
bundle exec rspec spec/system/<name>_spec.rb
```

## Rules

- One controller per responsibility
- Use **`static targets`**, **`static values`**, **`static classes`**, **`static outlets`** APIs
- Use **`<value>Changed`** callbacks for reactive updates instead of imperative DOM manipulation
- Clean up listeners in `disconnect()` if added in `connect()`
- NO direct `document.querySelector` — use `this.<name>Target`
- NO inline event handlers — use `data-action` attributes
- NO global state — all state lives on `static values`
- Filename matches data-controller name: `dropdown` → `dropdown_controller.js`
- Multi-word names: `infinite-scroll` → `infinite_scroll_controller.js`

## Output

```
Created:
  app/javascript/controllers/dropdown_controller.js
  spec/system/dropdown_spec.rb

To wire it up in HTML:
  data-controller="dropdown" data-dropdown-open-value="false"

Verified:
  bundle exec rspec  -- PASS (X examples, 0 failures)
```
