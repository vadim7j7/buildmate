---
name: new-turbo-stream
description: Add Turbo Stream broadcasts or controller responses for real-time DOM updates
---

# /new-turbo-stream

## What This Does

Generates a Turbo Stream — either as a controller response (`*.turbo_stream.erb`)
or as a model broadcast (`broadcasts_to`) — so server-side changes update the DOM
without a full page reload.

## Usage

```
/new-turbo-stream Comment create     # Controller response on create
/new-turbo-stream Comment broadcast  # Model-level broadcast on save/destroy
/new-turbo-stream Notification append --to=notifications
```

## How It Works

### 1. Read Patterns

- `patterns/hotwire-patterns.md`
- `patterns/forms-patterns.md`

### 2. Choose the Broadcast Style

| Style | Use when |
|-------|----------|
| **Controller response** (`format.turbo_stream`) | The triggering user is the only one who needs the update |
| **Model broadcast** (`broadcasts_to`) | All connected users need to see the change in real time |

### 3a. Controller Response Pattern

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

### 3b. Model Broadcast Pattern

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

### 4. Available Stream Actions

| Action | Effect |
|--------|--------|
| `turbo_stream.append` | Add to end |
| `turbo_stream.prepend` | Add to start |
| `turbo_stream.replace` | Replace the whole element |
| `turbo_stream.update` | Replace inner HTML, keep wrapper |
| `turbo_stream.remove` | Delete the element |
| `turbo_stream.before` / `.after` | Insert sibling |
| `turbo_stream.refresh` | Tell page to re-render via morphing (Turbo 8+) |

### 5. Generate System Spec

```ruby
RSpec.describe 'Comment posting', type: :system, js: true do
  let(:user) { create(:user) }
  let(:post_record) { create(:post) }

  before { sign_in user }

  it 'appends a comment without page reload' do
    visit post_path(post_record)

    fill_in 'Comment', with: 'Great post!'
    click_button 'Post comment'

    expect(page).to have_css("##{"comments_for_post_#{post_record.id}"} li", text: 'Great post!')
    expect(page).not_to have_field('Comment', with: 'Great post!') # form was reset
  end
end
```

## Rules

- Always use **stable target IDs** — `comments_for_post_<post_id>`, `notification_<id>`
- **Reset forms after success** — replace the form partial with a fresh one
- **Update counts and badges** in the same stream when relevant
- For broadcasts, scope the channel to the parent record: `broadcasts_to ->(c) { [c.post, :comments] }`
- For controller responses, ALSO provide an `html` fallback for clients without Turbo
- Use `status: :unprocessable_entity` on validation failure even in turbo_stream responses
- Make broadcast partials **self-contained** — they render outside the original request context (no `current_user`, no flash)

## Common Pitfalls

- **Form doesn't reset after submit**: include a `turbo_stream.replace "new_<x>_form"` action
- **Broadcast partial errors**: don't use helpers that depend on the request (no `current_user`, no `link_to_unless_current`)
- **Subscribers don't update**: ensure the view has `turbo_stream_from <record>, <stream_name>` matching the model's `broadcasts_to`
- **Duplicate elements appear**: if both controller response AND model broadcast fire for the same action, the user sees double — pick one

## Output

```
Modified / Created:
  app/views/comments/create.turbo_stream.erb         (controller stream view)
  app/models/comment.rb                              (broadcasts_to, if model broadcast)
  spec/system/comment_posting_spec.rb                (system spec)

Verified:
  bundle exec rspec  -- PASS
```
