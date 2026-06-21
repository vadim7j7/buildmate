# Form Patterns

Forms in a Rails monolith use `form_with` (Turbo-aware by default), render
errors with `role="alert"` for accessibility, and rely on the controller
returning **422 Unprocessable Entity** on validation failure so Turbo re-renders
the form with errors.

## Basic Form (model-backed)

```erb
<%= form_with(model: @profile, class: "space-y-4") do |form| %>
  <% if @profile.errors.any? %>
    <div role="alert" class="rounded bg-red-50 border border-red-200 p-3">
      <h2 class="font-semibold text-red-800">
        <%= t('errors.messages.validation_failed', count: @profile.errors.count) %>
      </h2>
      <ul class="mt-2 list-disc list-inside text-sm text-red-700">
        <% @profile.errors.full_messages.each do |msg| %>
          <li><%= msg %></li>
        <% end %>
      </ul>
    </div>
  <% end %>

  <div>
    <%= form.label :name, class: "block text-sm font-medium" %>
    <%= form.text_field :name, required: true,
                                class: "mt-1 block w-full rounded border-gray-300" %>
  </div>

  <%= form.submit class: "px-4 py-2 bg-blue-600 text-white rounded" %>
<% end %>
```

## Controller (Turbo-aware)

```ruby
def create
  @profile = current_user.profiles.build(profile_params)

  if @profile.save
    redirect_to @profile, notice: t('profiles.create.success')
  else
    render :new, status: :unprocessable_entity   # ← REQUIRED for Turbo
  end
end
```

If you forget `status: :unprocessable_entity`, Turbo treats the response as
success and does nothing — the form appears unchanged and the user has no idea
why submission "failed."

## Form Inside a Turbo Frame

```erb
<%= turbo_frame_tag "profile_form" do %>
  <%= form_with(model: @profile) do |form| %>
    ...
  <% end %>
<% end %>
```

The frame swap happens automatically on submit — both success and 422 responses
update the frame in place.

## Form Component (reusable)

For forms that appear in multiple places (new + edit + inline frame):

```erb
<%= render(ProfileFormComponent.new(profile: @profile)) %>
```

See `/new-form-component` for the full pattern.

## Field Helpers

| Field type | Helper |
|------------|--------|
| Text | `form.text_field :name` |
| Email | `form.email_field :email` |
| Password | `form.password_field :password` |
| Textarea | `form.text_area :bio, rows: 4` |
| Number | `form.number_field :age, min: 0, step: 1` |
| Date | `form.date_field :born_on` |
| Datetime | `form.datetime_local_field :starts_at` |
| Select | `form.select :status, Profile.statuses.keys` |
| Collection select | `form.collection_select :company_id, Company.all, :id, :name` |
| Checkbox | `form.check_box :active` |
| Radio | `form.radio_button :tier, "free"` |
| Hidden | `form.hidden_field :token` |
| File | `form.file_field :avatar, accept: "image/*"` |

## Nested Attributes

For one-to-many associations:

```ruby
class Profile < ApplicationRecord
  has_many :links, dependent: :destroy
  accepts_nested_attributes_for :links, allow_destroy: true, reject_if: :all_blank
end
```

```ruby
def profile_params
  params.require(:profile).permit(:name, links_attributes: %i[id url label _destroy])
end
```

```erb
<%= form_with(model: @profile) do |form| %>
  ...

  <div data-controller="nested-fields">
    <%= form.fields_for :links do |link_form| %>
      <div class="flex gap-2 items-center">
        <%= link_form.text_field :label, placeholder: 'Label' %>
        <%= link_form.url_field :url, placeholder: 'https://...' %>
        <%= link_form.check_box :_destroy %>
        <%= link_form.label :_destroy, 'Remove' %>
      </div>
    <% end %>
  </div>
<% end %>
```

For dynamically adding/removing fields, write a Stimulus controller (see
`patterns/stimulus-patterns.md`).

## File Upload (Active Storage)

```ruby
class Profile < ApplicationRecord
  has_one_attached :avatar
end
```

```ruby
def profile_params
  params.require(:profile).permit(:name, :avatar)
end
```

```erb
<%= form_with(model: @profile, multipart: true) do |form| %>
  <%= form.label :avatar %>
  <%= form.file_field :avatar, accept: "image/*",
                       direct_upload: true %>

  <% if @profile.avatar.attached? %>
    <%= image_tag @profile.avatar, class: "w-24 h-24 rounded" %>
  <% end %>
<% end %>
```

`direct_upload: true` uploads to S3/storage directly from the browser, bypassing
the Rails server for the upload itself.

## Form Object Pattern

When a form spans multiple models or doesn't map cleanly to one model, use a
form object:

```ruby
# app/forms/onboarding_form.rb
# frozen_string_literal: true

class OnboardingForm
  include ActiveModel::Model
  include ActiveModel::Attributes

  attribute :first_name, :string
  attribute :last_name, :string
  attribute :company_name, :string
  attribute :role, :string

  validates :first_name, :last_name, presence: true
  validates :role, inclusion: { in: %w[founder employee contractor] }

  def save
    return false unless valid?

    ActiveRecord::Base.transaction do
      user = User.create!(first_name:, last_name:)
      company = Company.create!(name: company_name)
      Membership.create!(user:, company:, role:)
    end

    true
  rescue ActiveRecord::RecordInvalid
    false
  end
end
```

```ruby
class OnboardingController < ApplicationController
  def new
    @form = OnboardingForm.new
  end

  def create
    @form = OnboardingForm.new(form_params)

    if @form.save
      redirect_to dashboard_path, notice: t('onboarding.success')
    else
      render :new, status: :unprocessable_entity
    end
  end

  private

  def form_params
    params.require(:onboarding_form).permit(:first_name, :last_name, :company_name, :role)
  end
end
```

The view treats it like any model:

```erb
<%= form_with(model: @form, url: onboarding_path) do |form| %>
  ...
<% end %>
```

## CSRF

Rails includes CSRF protection by default. `form_with` automatically includes the
authenticity token. Don't disable `protect_from_forgery` in HTML controllers.

If a controller is API-only (and you've authenticated via token/session
differently), it can skip CSRF:

```ruby
class Api::V1::BaseController < ActionController::API
  # API mode skips CSRF; ActionController::Base would need:
  # skip_before_action :verify_authenticity_token
end
```

## Style Rules

1. **Always use `form_with`** — never `form_for` or `form_tag`
2. **Always render with `status: :unprocessable_entity` on validation failure**
3. **Wrap error display in `role="alert"`** for screen readers
4. **Always pair labels with fields** — visible or `sr-only`
5. **Use `required:` on truly required fields** (browser will block submit)
6. **Never `params.permit!`** — explicit permit list always
7. **Use `t('...')` for all labels and error messages**
8. **Add `multipart: true`** when accepting file uploads
9. **Disable submit button while submitting** — Turbo does this automatically
10. **Use a form object** when no single model fits

## Common Pitfalls

| Symptom | Likely cause |
|---------|--------------|
| Form silently does nothing on validation failure | Missing `status: :unprocessable_entity` |
| Errors don't render | `@profile.errors.any?` is false because `valid?` wasn't called or `save` returned `true` |
| File upload missing in params | Form is missing `multipart: true` |
| `param is missing` error | Form name doesn't match `params.require(...)` argument |
| CSRF token errors | Disabled `protect_from_forgery` or removed CSRF meta tag |
