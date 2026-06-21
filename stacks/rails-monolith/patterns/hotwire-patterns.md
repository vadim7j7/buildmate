# Hotwire Patterns (Turbo Frames + Streams)

Turbo gives you SPA-like UX without writing client-side routing or state. This
file covers Turbo Drive (default), Turbo Frames (per-section navigation), and
Turbo Streams (server-pushed DOM updates).

For Stimulus, see `patterns/stimulus-patterns.md`.

---

## Turbo Drive (default behavior)

Every link click and form submit is intercepted by Turbo, fetched via XHR, and
the page is morphed in. **You don't have to do anything to use it** — it's on
by default in `turbo-rails`.

To opt out for a specific link or form:

```erb
<%= link_to 'Download', report_path, data: { turbo: false } %>
<%= form_with(model: @user, data: { turbo: false }) do |form| ... %>
```

Reasons to opt out: file downloads, third-party redirects, legacy pages that
don't play well with Turbo.

---

## Turbo Frames

A `<turbo-frame>` element scopes navigation to its contents. Links and forms
inside it update only the frame, not the whole page.

### Eager Frame (content rendered inline)

```erb
<!-- app/views/profiles/show.html.erb -->
<%= turbo_frame_tag "profile_#{@profile.id}" do %>
  <%= render(ProfileCardComponent.new(profile: @profile)) %>
  <%= link_to t('common.edit'), edit_profile_path(@profile) %>
<% end %>
```

The `edit` view contains a matching frame:

```erb
<!-- app/views/profiles/edit.html.erb -->
<%= turbo_frame_tag "profile_#{@profile.id}" do %>
  <%= render(ProfileFormComponent.new(profile: @profile)) %>
<% end %>
```

When the user clicks "Edit", Turbo fetches `/profiles/:id/edit`, extracts the
matching frame, and swaps it in. URL doesn't change.

### Lazy Frame (deferred load)

```erb
<%= turbo_frame_tag "notifications", src: notifications_path, loading: :lazy do %>
  <div class="animate-pulse h-24 bg-gray-100 rounded"></div>
<% end %>
```

The block content is the loading-state placeholder. When the frame is visible,
Turbo fetches `src=` and replaces the contents.

### Breaking out of a Frame

If a link inside a frame should navigate the WHOLE page (not just the frame):

```erb
<%= link_to 'View profile', profile_path(@profile), data: { turbo_frame: '_top' } %>
```

`_top` targets the whole document. Use a custom frame ID to target a different frame.

### Frame Rules

- **Frame IDs must be unique** within the page
- Use stable, descriptive IDs: `profile_42`, `comments_for_post_7`, `notifications`
- The response MUST include a frame with the same ID, or the user sees "Content missing"
- Lazy frames need loading-state markup inside the block
- Don't nest frames unless there's a clear reason

---

## Turbo Streams

Streams update the DOM after a request without a full page reload. Use them when
the server has new state to communicate.

### Controller Stream Response

```ruby
# app/controllers/comments_controller.rb
def create
  @post = Post.find(params[:post_id])
  @comment = @post.comments.build(comment_params.merge(user: current_user))

  if @comment.save
    respond_to do |format|
      format.turbo_stream  # renders create.turbo_stream.erb
      format.html { redirect_to @post }
    end
  else
    respond_to do |format|
      format.turbo_stream do
        render turbo_stream: turbo_stream.replace(
          "new_comment_form",
          partial: "comments/form",
          locals: { post: @post, comment: @comment }
        ), status: :unprocessable_entity
      end
      format.html { redirect_to @post, alert: @comment.errors.full_messages.to_sentence }
    end
  end
end
```

```erb
<!-- app/views/comments/create.turbo_stream.erb -->
<%= turbo_stream.append "comments_for_post_#{@post.id}",
                        partial: "comments/comment",
                        locals: { comment: @comment } %>
<%= turbo_stream.replace "new_comment_form",
                          partial: "comments/form",
                          locals: { post: @post, comment: Comment.new } %>
<%= turbo_stream.update "comment_count", @post.comments.count %>
```

### Available Stream Actions

| Action | Effect |
|--------|--------|
| `turbo_stream.append`  | Insert at end of target |
| `turbo_stream.prepend` | Insert at start of target |
| `turbo_stream.replace` | Replace the target element entirely |
| `turbo_stream.update`  | Replace inner HTML, keep wrapper |
| `turbo_stream.remove`  | Delete the target |
| `turbo_stream.before`  | Insert as sibling before |
| `turbo_stream.after`   | Insert as sibling after |
| `turbo_stream.refresh` | Trigger page-level morph (Turbo 8+) |

### Model Broadcasts

For real-time updates pushed to all subscribers (chat, live feed, dashboards):

```ruby
# app/models/comment.rb
class Comment < ApplicationRecord
  belongs_to :post
  belongs_to :user

  broadcasts_to ->(comment) { [comment.post, :comments] },
                inserts_by: :append,
                target: ->(comment) { "comments_for_post_#{comment.post_id}" },
                partial: "comments/comment"
end
```

The view subscribes:

```erb
<%= turbo_stream_from @post, :comments %>
<div id="comments_for_post_<%= @post.id %>">
  <%= render @post.comments %>
</div>
```

This requires ActionCable to be wired up.

### Broadcast Partial Constraints

Broadcast partials render OUTSIDE the original request — they don't have:
- `current_user`
- `flash`
- request-bound helpers like `link_to_unless_current`

Either avoid those helpers in broadcasted partials, or pass any needed user
context into the partial via locals.

---

## Page Refresh & Morphing (Turbo 8+)

```ruby
respond_to do |format|
  format.turbo_stream { render turbo_stream: turbo_stream.refresh }
  format.html { redirect_to @profile }
end
```

This re-renders the page using DOM morphing — preserving scroll position and
focus while updating only changed elements. Useful for actions that affect
multiple unrelated parts of the page.

---

## Decision Tree

```
Need to update part of the page after a server action?

├── Same user, single section → Turbo Frame (eager or lazy)
├── Same user, multiple sections → format.turbo_stream + multiple stream actions
├── All connected users → Model.broadcasts_to + turbo_stream_from in view
└── Page-wide morph after complex change → turbo_stream.refresh (Turbo 8+)
```

---

## Common Pitfalls

| Symptom | Likely cause |
|---------|--------------|
| "Content missing" error | Response doesn't contain a frame with matching ID |
| Form posts the whole page | Form is outside the frame — wrap it or set `data-turbo-frame="<id>"` |
| Form fails silently on validation error | Controller returned 200 instead of 422 — use `:unprocessable_entity` |
| DELETE redirects re-issue DELETE | Controller returned 302 instead of 303 — use `:see_other` |
| Broadcast partial errors out | Partial uses `current_user` or other request-bound helpers |
| Subscribers don't update | View missing `turbo_stream_from`, or stream name mismatch |
| Duplicate items appear | Both controller stream AND model broadcast fire — pick one |

---

## Style Rules

1. **Stable, descriptive frame IDs** — `comments_for_post_<id>`, never `frame_1`
2. **Always provide loading state** for lazy frames
3. **Reset forms after success** — replace the form partial in the stream response
4. **Update related elements** in the same stream (counts, badges, summaries)
5. **Always provide HTML fallback** alongside `format.turbo_stream`
6. **422 on validation failure**, **303 on DELETE redirect**
7. **Broadcast partials must be self-contained** — no request-bound helpers
8. **Don't nest frames** unless absolutely needed
