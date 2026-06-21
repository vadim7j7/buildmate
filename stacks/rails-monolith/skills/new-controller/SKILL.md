---
name: new-controller
description: Generate a Rails controller with HTML views, JSON support, and full RESTful actions
---

# /new-controller

## What This Does

Generates a new RESTful controller for the **monolith**: HTML by default, JSON when
needed. Includes routes, strong params, before_actions for auth + resource loading,
and Turbo-aware redirect statuses.

## Usage

```
/new-controller Profiles            # Creates ProfilesController (HTML primary)
/new-controller Admin::Companies    # Creates Admin::CompaniesController
/new-controller Profiles --api      # Creates Api::V1::ProfilesController (JSON only)
```

## How It Works

1. **Read reference patterns.** Load:
   - `patterns/rails-monolith-patterns.md`
   - `patterns/forms-patterns.md`
   - `patterns/flash-and-redirect-patterns.md`
   - `styles/erb-style.md`

2. **Determine namespace + class name.** Parse the argument:
   - `Profiles` → `ProfilesController` (HTML primary)
   - `Admin::Companies` → `Admin::CompaniesController`
   - `Profiles --api` → `Api::V1::ProfilesController` (JSON only)

3. **Generate the controller file.** Create with:
   - `frozen_string_literal: true`
   - RESTful actions: `index`, `show`, `new`, `create`, `edit`, `update`, `destroy`
   - `before_action :authenticate_user!`
   - `before_action :set_<resource>` for member actions
   - `before_action :authorize_<resource>!` for mutations
   - `respond_to :html, :json` if both formats supported
   - Strong params method
   - **Turbo-compatible status codes** (`:unprocessable_entity` on validation, `:see_other` on DELETE)

4. **Generate ERB views** (HTML controllers only): `index`, `show`, `new`, `edit`, `_form` partial

5. **Generate request spec** with both HTML and JSON paths (when applicable)

6. **Add route.** Suggest the `resources` line for `config/routes.rb`.

7. **Run quality checks.**

   ```bash
   bundle exec rubocop -A app/controllers/<path>.rb spec/requests/<path>_spec.rb
   bundle exec rspec spec/requests/<path>_spec.rb
   ```

## Generated Files

```
app/controllers/<namespace>/<resource>_controller.rb
app/views/<resource>/index.html.erb
app/views/<resource>/show.html.erb
app/views/<resource>/new.html.erb
app/views/<resource>/edit.html.erb
app/views/<resource>/_form.html.erb
spec/requests/<resource>_spec.rb
```

## Controller Template (HTML primary)

```ruby
# frozen_string_literal: true

class ProfilesController < ApplicationController
  before_action :authenticate_user!
  before_action :set_profile, only: %i[show edit update destroy]
  before_action :authorize_profile!, only: %i[edit update destroy]

  def index
    @profiles = current_user.profiles.includes(:company).page(params[:page])
  end

  def show; end

  def new
    @profile = current_user.profiles.build
  end

  def create
    @profile = current_user.profiles.build(profile_params)

    if @profile.save
      redirect_to @profile, notice: t('profiles.create.success')
    else
      render :new, status: :unprocessable_entity
    end
  end

  def edit; end

  def update
    if @profile.update(profile_params)
      redirect_to @profile, notice: t('profiles.update.success')
    else
      render :edit, status: :unprocessable_entity
    end
  end

  def destroy
    @profile.destroy!
    redirect_to profiles_path, notice: t('profiles.destroy.success'), status: :see_other
  end

  private

  def set_profile
    @profile = current_user.profiles.find(params[:id])
  end

  def authorize_profile!
    head :forbidden unless @profile.user == current_user
  end

  def profile_params
    params.require(:profile).permit(:name, :email, :bio, :company_id)
  end
end
```

## Rules

- Default to HTML; only generate `respond_to do |format|` blocks when JSON is also needed
- Use **instance variables** (`@profile`) to pass data to views — NOT local variables
- **Always** use `status: :unprocessable_entity` on form validation failure
- **Always** use `status: :see_other` on DELETE redirects
- Use `t('...')` for flash messages
- Scope queries through `current_user` for authorization-by-default
- Use strong params with explicit `permit` list
- Use `includes()` to prevent N+1 queries

## Output

```
Created:
  app/controllers/profiles_controller.rb
  app/views/profiles/{index,show,new,edit}.html.erb
  app/views/profiles/_form.html.erb
  spec/requests/profiles_spec.rb

Suggested route addition (config/routes.rb):
  resources :profiles

Verified:
  bundle exec rubocop  -- PASS
  bundle exec rspec    -- PASS (X examples, 0 failures)
```
