---
name: new-turbo-frame
description: Wrap a section of a page in a Turbo Frame for independent navigation/refresh
---

# /new-turbo-frame

## What This Does

Adds a Turbo Frame around a section of the page so its content can be replaced
independently — without a full page reload — when navigated or when the matching
frame is rendered by another response.

## Usage

```
/new-turbo-frame profile_<id>           # Lazy/eager frame for a single resource
/new-turbo-frame comments_for_post_<id> # Frame containing a list
/new-turbo-frame --lazy notifications   # Lazy-load the frame's content
```

## How It Works

### 1. Read Patterns

Before generating, read:
- `patterns/hotwire-patterns.md`
- `patterns/forms-patterns.md` (for form-in-frame interactions)

### 2. Decide the Frame Strategy

| Strategy | Use when |
|----------|----------|
| **Eager frame** (content rendered inline) | Content is already on the page; just want navigation to swap it |
| **Lazy frame** (`src=` set, loaded async) | Content is expensive; defer until visible |
| **Loading-shell frame** | Show skeleton/spinner while the lazy frame fetches |

### 3. Generate the Frame Markup

#### Eager (inline content)

```erb
<%= turbo_frame_tag "profile_#{@profile.id}" do %>
  <%= render(ProfileCardComponent.new(profile: @profile)) %>
  <div class="mt-2">
    <%= link_to t('common.edit'), edit_profile_path(@profile), class: "text-blue-600" %>
  </div>
<% end %>
```

The matching `edit` view ALSO renders that frame ID, so clicking the link swaps
just this section:

```erb
<!-- app/views/profiles/edit.html.erb -->
<%= turbo_frame_tag "profile_#{@profile.id}" do %>
  <%= render "form", profile: @profile %>
<% end %>
```

#### Lazy (deferred load)

```erb
<%= turbo_frame_tag "notifications", src: notifications_path, loading: :lazy do %>
  <div class="animate-pulse h-24 bg-gray-100 rounded"></div>
<% end %>
```

The `notifications` action renders just the matching frame:

```erb
<!-- app/views/notifications/index.html.erb -->
<%= turbo_frame_tag "notifications" do %>
  <% @notifications.each do |notification| %>
    <%= render(NotificationItemComponent.new(notification:)) %>
  <% end %>
<% end %>
```

### 4. Suggest Controller Changes (if needed)

If the frame loads from a URL, ensure the rendering action exists and the route
is correct. Print the suggested route:

```
get "/notifications", to: "notifications#index"
```

### 5. Verify with a System Spec

```ruby
RSpec.describe 'Profile frame edit', type: :system, js: true do
  let(:user) { create(:user) }
  let!(:profile) { create(:profile, user:, name: 'Old name') }
  before { sign_in user }

  it 'swaps the frame in place when editing' do
    visit profile_path(profile)
    expect(page).to have_text('Old name')

    within "turbo-frame#profile_#{profile.id}" do
      click_link 'Edit'
    end

    expect(page).to have_current_path(profile_path(profile))
    fill_in 'Name', with: 'New name'
    click_button 'Save'

    expect(page).to have_text('New name')
  end
end
```

## Rules

- Frame IDs must be **unique within the page**
- Use stable, descriptive IDs: `profile_42`, `comments_for_post_7`, `notifications`
- For collections: namespace with the parent record (`comments_for_post_<id>`)
- Lazy frames should provide loading-state markup inside the block
- Links/forms inside a frame target the SAME frame by default — to break out, set `data-turbo-frame="_top"`
- The matching response MUST contain a frame with the same ID, or Turbo will display a "Content missing" error
- Do NOT nest frames unless you have a clear reason

## Common Pitfalls

- **"Content missing" error**: the response doesn't contain a frame with that ID
- **Form posts the wrong frame**: add `data-turbo-frame="_top"` on the form to escape
- **Full page reload happens anyway**: check that the link is inside the frame, not outside it
- **Frame doesn't update after broadcast**: use `turbo_stream` (not just frames) for server-pushed updates

## Output

```
Modified:
  app/views/profiles/show.html.erb (wrapped section in turbo_frame_tag)
  app/views/profiles/edit.html.erb (wrapped form in matching turbo_frame_tag)

Created (if --lazy):
  spec/system/profile_frame_spec.rb

Verified:
  bundle exec rspec spec/system/profile_frame_spec.rb  -- PASS
```
