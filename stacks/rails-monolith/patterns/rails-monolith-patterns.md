# Rails Monolith Code Patterns

The default response format is **HTML rendered by Rails views**, with optional JSON
support via `respond_to`. ViewComponents handle reusable UI; Hotwire handles
interactivity. These patterns cover models, services, controllers, jobs, and helpers.

For view-layer patterns (ViewComponents, ERB, Stimulus, Turbo, forms), see:
- `patterns/view-component-patterns.md`
- `patterns/hotwire-patterns.md`
- `patterns/stimulus-patterns.md`
- `patterns/forms-patterns.md`
- `patterns/flash-and-redirect-patterns.md`

---

## 1. Model Pattern

```ruby
# frozen_string_literal: true

class Profile < ApplicationRecord
  # 1. Includes
  include Searchable
  has_paper_trail

  # 2. Constants
  STATUSES = %w[active inactive archived].freeze

  # 3. Associations
  belongs_to :user
  belongs_to :company, optional: true
  has_many :experiences, dependent: :destroy
  has_many :skills, through: :profile_skills

  # 4. Validations
  validates :name, presence: true, length: { maximum: 255 }
  validates :email, presence: true, uniqueness: { case_sensitive: false }

  # 5. Enums
  enum :status, { active: 0, inactive: 1, archived: 2 }, default: :active

  # 6. Scopes
  scope :active,    -> { where(status: :active) }
  scope :recent,    -> { order(created_at: :desc) }
  scope :search,    ->(q) { q.blank? ? all : where('name ILIKE ?', "%#{q}%") }

  # 7. Callbacks
  before_validation :normalize_email
  after_create_commit :enqueue_welcome_job

  # 8. Public methods
  def display_name
    "#{name} (#{company&.name || 'Independent'})"
  end

  private

  def normalize_email
    self.email = email&.strip&.downcase
  end

  def enqueue_welcome_job
    WelcomeJob.perform_later(id)
  end
end
```

Rules:
- Always specify `dependent:` on `has_many` and `has_one`
- Use `optional: true` on `belongs_to` when the FK is nullable
- Composable scopes: return `all` when filter is blank
- Use ILIKE (not LIKE) for case-insensitive Postgres search

---

## 2. Service Pattern

Services encapsulate business logic outside models and controllers.

```ruby
# frozen_string_literal: true

module Users
  class SyncProfileService < ApplicationService
    def initialize(user:, provider:)
      @user = user
      @provider = provider
    end

    def call
      return if user.synced_recently?

      sync_from_provider
    end

    private

    attr_reader :user, :provider

    def sync_from_provider
      # ...
    end
  end
end
```

Rules:
- Namespaced under a domain module
- Inherit from `ApplicationService`
- Keyword args in `initialize`
- Single public `call` method
- Guard clauses at the top
- Private `attr_reader` for instance vars

---

## 3. Controller Pattern (HTML-first, JSON-aware)

```ruby
# frozen_string_literal: true

class ProfilesController < ApplicationController
  before_action :authenticate_user!
  before_action :set_profile, only: %i[show edit update destroy]
  before_action :authorize_profile!, only: %i[edit update destroy]

  def index
    @profiles = current_user.profiles
      .includes(:company)
      .page(params[:page]).per(25)

    respond_to do |format|
      format.html
      format.json { render json: @profiles.map { |p| ProfilePresenter.new(p).call } }
    end
  end

  def show
  end

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

  def edit
  end

  def update
    if @profile.update(profile_params)
      redirect_to @profile, notice: t('profiles.update.success')
    else
      render :edit, status: :unprocessable_entity
    end
  end

  def destroy
    @profile.destroy!
    redirect_to profiles_path,
                notice: t('profiles.destroy.success'),
                status: :see_other
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

### Controller Rules

- RESTful actions: `index`, `show`, `new`, `create`, `edit`, `update`, `destroy`
- Set instance variables (`@profile`) for views
- Use `respond_to do |format|` only when both HTML and JSON are needed
- Use `redirect_to ..., notice:` and `redirect_to ..., alert:` for flash
- **Use `status: :unprocessable_entity` (422) on validation failure** — Turbo expects this
- **Use `status: :see_other` (303) on DELETE redirects** — Turbo expects this
- Scope through `current_user` for authorization-by-default
- Strong params with explicit `permit`
- `includes()` to prevent N+1 queries

---

## 4. Helper Pattern

Helpers are PRESENTATION ONLY. No DB queries. No business logic.

```ruby
# frozen_string_literal: true

module ProfilesHelper
  # @param profile [Profile]
  # @return [ActiveSupport::SafeBuffer]
  def profile_avatar(profile, size: :md)
    dimensions = case size
                 when :sm then 'w-6 h-6'
                 when :md then 'w-10 h-10'
                 when :lg then 'w-16 h-16'
                 end

    image_tag profile.avatar_url(size: size),
              class: "#{dimensions} rounded-full",
              alt: profile.name
  end

  # @param status [String]
  # @return [String]
  def profile_status_classes(status)
    base = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium'
    color = case status.to_s
            when 'active'   then 'bg-green-100 text-green-800'
            when 'inactive' then 'bg-gray-100 text-gray-800'
            when 'archived' then 'bg-red-100 text-red-800'
            end
    "#{base} #{color}"
  end
end
```

Rules:
- Format dates, currency, status labels
- Compute CSS classes from values
- Build small bits of HTML with `tag.div`, `image_tag`
- NO database queries
- NO business logic
- For complex computed HTML, prefer a ViewComponent

---

## 5. Presenter Pattern

In a monolith, presenters are useful for **JSON serialization** and for shaping
data passed to ViewComponents (when the shaping is non-trivial).

```ruby
# frozen_string_literal: true

class ProfilePresenter < BasePresenter
  def call
    {
      id: record.id,
      name: record.name,
      email: record.email,
      company: company_data,
      created_at: record.created_at.iso8601
    }
  end

  private

  def company_data
    return unless record.association_loaded?(:company) && record.company

    { id: record.company.id, name: record.company.name }
  end
end
```

For view-side data shaping that's specific to one component, prefer methods on
the ViewComponent itself.

---

## 6. Job Pattern

```ruby
# frozen_string_literal: true

module Sync
  class ImportJob < ApplicationJob
    queue_as :default
    sidekiq_options retry: 3

    retry_on Net::ReadTimeout, wait: :polynomially_longer, attempts: 5
    discard_on ActiveJob::DeserializationError

    def perform(import_id)
      import = Import.find(import_id)
      return if import.completed?

      Sync::ImportService.new(import:).call
    rescue ActiveRecord::RecordNotFound => e
      Rails.logger.warn("Import not found: #{e.message}")
    end
  end
end
```

Rules:
- Namespaced under a domain module
- Configure `queue_as` and `sidekiq_options retry:`
- Use `retry_on` for transient errors
- Use `discard_on` for unrecoverable errors
- Delegate to a service for complex logic
- Guard against already-processed records

---

## 7. Style Rules (MANDATORY)

1. **`frozen_string_literal: true`** - First line of every Ruby file
2. **Single quotes** - Always, unless interpolation
3. **Hash shorthand** - `{ id:, name: }` not `{ id: id, name: name }`
4. **Guard clauses** - `return if condition?` over nested conditionals
5. **YARD docs** - On public methods (especially helpers and components)
6. **`includes()`** - Always eager-load to prevent N+1
7. **Strong params** - Never `params.permit!`
8. **Instance vars in controllers** - Set `@variable` for views
9. **`status: :unprocessable_entity`** on validation failure
10. **`status: :see_other`** on DELETE redirects
11. **`t('...')` for user-visible strings** - Never hardcode English
12. **Snake_case** for methods/variables; CamelCase for classes/modules
