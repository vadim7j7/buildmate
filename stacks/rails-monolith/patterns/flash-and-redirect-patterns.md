# Flash and Redirect Patterns

Flash messages communicate the outcome of an action across a redirect. In a
Turbo-aware monolith, flash works for HTML redirects AND can be re-rendered via
Turbo Streams without a navigation.

## Setting Flash on Redirect

```ruby
def create
  @profile = current_user.profiles.build(profile_params)

  if @profile.save
    redirect_to @profile, notice: t('profiles.create.success')
  else
    render :new, status: :unprocessable_entity
  end
end

def destroy
  @profile.destroy!
  redirect_to profiles_path,
              notice: t('profiles.destroy.success'),
              status: :see_other
end
```

Conventional keys:
- `notice:` — neutral / success
- `alert:` — warning / failure
- `flash[:custom_key]` — for non-standard messages

## Status Codes (Turbo-Aware)

| Action result | Status code | Helper |
|---------------|-------------|--------|
| Successful create/update + redirect | 302 (default) | `redirect_to @profile, notice: ...` |
| Validation failure (re-render form) | **422** | `render :new, status: :unprocessable_entity` |
| Successful destroy + redirect | **303** | `redirect_to ..., status: :see_other` |
| Auth required | 401 | `head :unauthorized` |
| Forbidden | 403 | `head :forbidden` |

The 422 and 303 are critical for Turbo:
- **422 on form failure** so Turbo re-renders with errors
- **303 on DELETE redirect** so Turbo issues a GET (not a re-DELETE) on the redirect target

## Rendering Flash in the Layout

```erb
<!-- app/views/layouts/application.html.erb -->
<!DOCTYPE html>
<html>
  <head>...</head>
  <body>
    <%= render "shared/flash" %>
    <%= yield %>
  </body>
</html>
```

```erb
<!-- app/views/shared/_flash.html.erb -->
<% flash.each do |type, message| %>
  <%= render(FlashComponent.new(type: type.to_sym, message: message)) %>
<% end %>
```

## Flash ViewComponent

```ruby
# app/components/flash_component.rb
# frozen_string_literal: true

class FlashComponent < ApplicationComponent
  TYPES = %i[notice alert error info].freeze

  def initialize(type:, message:)
    @type = TYPES.include?(type) ? type : :notice
    @message = message
  end

  private

  attr_reader :type, :message

  def container_classes
    base = 'rounded p-3 border my-3'
    color = case type
            when :notice then 'bg-green-50 border-green-200 text-green-800'
            when :alert  then 'bg-yellow-50 border-yellow-200 text-yellow-800'
            when :error  then 'bg-red-50 border-red-200 text-red-800'
            when :info   then 'bg-blue-50 border-blue-200 text-blue-800'
            end
    "#{base} #{color}"
  end

  def role
    type == :error || type == :alert ? 'alert' : 'status'
  end
end
```

```erb
<!-- app/components/flash_component.html.erb -->
<div role="<%= role %>"
     class="<%= container_classes %>"
     data-controller="auto-dismiss"
     data-auto-dismiss-delay-value="5000">
  <%= message %>
</div>
```

## Auto-Dismiss Stimulus Controller

```js
// app/javascript/controllers/auto_dismiss_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = { delay: { type: Number, default: 5000 } }

  connect() {
    this.timeout = setTimeout(() => this.dismiss(), this.delayValue)
  }

  disconnect() {
    clearTimeout(this.timeout)
  }

  dismiss() {
    this.element.remove()
  }
}
```

## Flash via Turbo Stream

To show flash WITHOUT a redirect (e.g., from a Turbo Stream response):

```erb
<!-- app/views/comments/create.turbo_stream.erb -->
<%= turbo_stream.append "comments_for_post_#{@post.id}",
                        partial: "comments/comment",
                        locals: { comment: @comment } %>
<%= turbo_stream.prepend "flash",
                          partial: "shared/flash_message",
                          locals: { type: :notice, message: t('comments.create.success') } %>
```

The layout needs a `<div id="flash">` for the prepend target:

```erb
<body>
  <div id="flash"></div>
  <%= render "shared/flash" %>   <!-- for non-Turbo flash from controller redirects -->
  <%= yield %>
</body>
```

## Helper for Setting Flash from Controllers

```ruby
# app/controllers/concerns/flashable.rb
module Flashable
  extend ActiveSupport::Concern

  private

  # @param notice [String, nil]
  # @param alert [String, nil]
  def flash_now(notice: nil, alert: nil)
    flash.now[:notice] = notice if notice
    flash.now[:alert]  = alert  if alert
  end
end
```

Use `flash.now` when re-rendering (no redirect); use `flash` when redirecting.

## Style Rules

1. **Always use translation keys** — `notice: t('profiles.create.success')`
2. **422 on validation failure**, **303 on DELETE redirect**
3. **`role="alert"`** for error/warning flash; **`role="status"`** for notice/info
4. **`flash.now`** when re-rendering, **`flash`** when redirecting
5. **Flash messages should be 1 line** — for longer feedback, render a banner inside the page
6. **Don't store sensitive data in flash** — it's stored in the session
7. **Use a `FlashComponent`** for consistent styling across the app

## Common Pitfalls

| Symptom | Likely cause |
|---------|--------------|
| Form re-render shows no errors AND no flash | Used `render :new` without `status: :unprocessable_entity` |
| Flash shows twice after redirect | Both controller AND turbo_stream rendered it |
| Flash persists across pages | Used `flash[:notice]` instead of `flash.now[:notice]` on a render |
| Delete causes infinite loop / re-deletion | Missing `status: :see_other` on the redirect after DELETE |
| Flash doesn't auto-dismiss | Auto-dismiss controller missing or `delay-value` not set |
