# Rails Backend Code Patterns

Comprehensive code patterns for the Rails backend. All agents must follow these
patterns when writing or reviewing code. Based on production Rails conventions.

---

## 1. Model Pattern

Models follow a strict internal ordering and use ActiveRecord features consistently.

### Structure

```ruby
# frozen_string_literal: true

# YARD class-level documentation describing what this model represents.
#
# @!attribute name [rw]
#   @return [String] description
class ModelName < ApplicationRecord
  # 1. Includes / Extensions
  include Searchable
  has_paper_trail

  # 2. Constants
  STATUSES = %w[active inactive archived].freeze

  # 3. Associations (belongs_to first, then has_many, has_one)
  belongs_to :user
  belongs_to :company, optional: true
  has_many :items, dependent: :destroy
  has_many :tags, through: :item_tags
  has_one :setting, dependent: :destroy

  # 4. Validations
  validates :name, presence: true, length: { maximum: 255 }
  validates :email, presence: true, uniqueness: { case_sensitive: false }

  # 5. Enums
  enum :status, { active: 0, inactive: 1, archived: 2 }, default: :active

  # 6. Scopes
  scope :active, -> { where(status: :active) }
  scope :recent, -> { order(created_at: :desc) }
  scope :search, ->(query) {
    return all if query.blank?

    where('name ILIKE ?', "%#{query}%")
  }

  # 7. Callbacks
  before_validation :normalize_attributes
  after_create_commit :enqueue_welcome_job

  # 8. Public methods
  def display_name
    "#{name} (#{company&.name || 'Independent'})"
  end

  # 9. Private methods
  private

  def normalize_attributes
    self.email = email&.strip&.downcase
  end

  def enqueue_welcome_job
    WelcomeJob.perform_later(id)
  end
end
```

### Association Rules

- Always specify `dependent:` on `has_many` and `has_one`
- Use `optional: true` on `belongs_to` when the foreign key can be null
- Use `through:` for many-to-many relationships
- Use `has_paper_trail` for models that need audit history

### Validation Rules

- `presence: true` on all required fields
- `uniqueness:` with `case_sensitive: false` for emails
- `length:` constraints on all string fields
- `format:` with regex for structured fields (email, phone)
- `inclusion:` for fields with known value sets

### Scope Rules

- Return `all` when filter parameter is blank (composable scopes)
- Use ILIKE for case-insensitive text search (PostgreSQL)
- Name scopes as adjectives or prepositional phrases

---

## 2. Service Pattern

Services encapsulate business logic outside of models and controllers.

### Structure

```ruby
# frozen_string_literal: true

module Namespace
  # YARD documentation describing what this service does and when to use it.
  #
  # @example
  #   Namespace::ServiceName.new(param:).call
  class ServiceName < ApplicationService
    # @param param [Type] description
    def initialize(param:, optional_param: nil)
      @param = param
      @optional_param = optional_param
    end

    # Description of what call does.
    #
    # @return [Type] description
    def call
      return early_value if guard_condition?

      perform_main_logic
    end

    private

    attr_reader :param, :optional_param

    def guard_condition?
      # Return true to skip execution
    end

    def perform_main_logic
      # Core business logic
    end
  end
end
```

### Service Rules

- Namespaced under a domain module (`Users::`, `BulkImport::`, `Sync::`)
- Inherits from `ApplicationService`
- `initialize` uses keyword arguments only
- Single public method: `call`
- Guard clauses at the top of `call`
- Private `attr_reader` for all instance variables
- Returns meaningful values (result objects, booleans, data)
- Rescues specific exceptions only

### ApplicationService Base

```ruby
# frozen_string_literal: true

class ApplicationService
  def self.call(...)
    new(...).call
  end
end
```

---

## 3. Presenter Pattern

Presenters serialize model data for API responses.

### Structure

```ruby
# frozen_string_literal: true

# YARD documentation describing what data this presenter serializes.
class ModelPresenter < BasePresenter
  # @return [Hash, Array<Hash>] serialized data
  def call
    if record.respond_to?(:each)
      record.map { |r| present_one(r) }
    else
      present_one(record)
    end
  end

  private

  def present_one(item)
    {
      id: item.id,
      name: item.name,
      # Use hash shorthand for direct attribute mapping
      nested: nested_data(item),
      created_at: item.created_at.iso8601
    }
  end

  def nested_data(item)
    return unless item.association_loaded?(:related) && item.related

    { id: item.related.id, name: item.related.name }
  end
end
```

### Presenter Rules

- Inherits from `BasePresenter`
- Single public method: `call`
- Handles both single records and collections
- Uses `iso8601` for all timestamp formatting
- Returns `nil` for absent optional associations (not empty hash)
- Never triggers additional database queries (data must be preloaded)

---

## 4. Controller Pattern

Controllers handle HTTP requests and delegate to services/presenters.

### Structure

```ruby
# frozen_string_literal: true

module Api
  module V1
    class ResourcesController < BaseController
      before_action :authenticate_user!
      before_action :set_resource, only: %i[show update destroy]

      def index
        resources = scope
          .includes(:association1, :association2)
          .page(params[:page])
          .per(params[:per_page] || 25)

        render json: {
          resources: ResourcePresenter.new(resources).call,
          meta: pagination_meta(resources)
        }
      end

      def show
        render json: ResourcePresenter.new(@resource).call
      end

      def create
        resource = scope.build(resource_params)

        if resource.save
          render json: ResourcePresenter.new(resource).call, status: :created
        else
          render json: { errors: resource.errors.full_messages }, status: :unprocessable_entity
        end
      end

      def update
        if @resource.update(resource_params)
          render json: ResourcePresenter.new(@resource).call
        else
          render json: { errors: @resource.errors.full_messages }, status: :unprocessable_entity
        end
      end

      def destroy
        @resource.destroy!
        head :no_content
      end

      private

      def scope
        current_user.resources
      end

      def set_resource
        @resource = scope.find(params[:id])
      end

      def resource_params
        params.require(:resource).permit(:attr1, :attr2, :attr3)
      end
    end
  end
end
```

### Controller Rules

- RESTful actions only (index, show, create, update, destroy)
- `before_action :authenticate_user!` on all actions (unless explicitly public)
- Scope resources through `current_user` for authorization
- Use strong params with explicit `permit` list
- Use presenters for all JSON responses
- Include `pagination_meta` on all list endpoints
- Use `includes()` to prevent N+1 queries
- Error responses use `errors.full_messages`

---

## 5. Job Pattern

Jobs handle background processing with Sidekiq.

### Structure

```ruby
# frozen_string_literal: true

module Namespace
  # YARD documentation describing what this job does.
  class JobName < ApplicationJob
    queue_as :queue_name
    sidekiq_options retry: 3

    retry_on SpecificError, wait: :polynomially_longer, attempts: 5
    discard_on ActiveJob::DeserializationError

    # @param record_id [Integer] the record to process
    def perform(record_id)
      record = Model.find(record_id)
      return if record.already_processed?

      Namespace::ServiceName.new(record:).call
    rescue ActiveRecord::RecordNotFound => e
      Rails.logger.warn("Record not found: #{e.message}")
    end
  end
end
```

### Job Rules

- Namespaced under a domain module
- Always configure `queue_as` and `sidekiq_options retry:`
- Use `retry_on` for transient errors (network, deadlocks)
- Use `discard_on` for unrecoverable errors
- Delegate to a service for complex logic
- Guard against already-processed records
- Log errors with context, do not silently swallow

---

## 6. Query Object Pattern

For complex database queries that do not belong in scopes.

### Structure

```ruby
# frozen_string_literal: true

class Namespace::SearchQuery < ApplicationQuery
  def initialize(params:, scope: Model.all)
    @params = params
    @scope = scope
  end

  # @return [ActiveRecord::Relation]
  def call
    @scope
      .then { |s| filter_by_status(s) }
      .then { |s| filter_by_category(s) }
      .then { |s| apply_search(s) }
      .then { |s| apply_sorting(s) }
      .includes(:association)
  end

  private

  attr_reader :params

  def filter_by_status(scope)
    return scope if params[:status].blank?
    scope.where(status: params[:status])
  end

  def apply_search(scope)
    return scope if params[:q].blank?
    scope.where('name ILIKE ?', "%#{params[:q]}%")
  end

  def apply_sorting(scope)
    case params[:sort]
    when 'name' then scope.order(:name)
    when 'recent' then scope.order(created_at: :desc)
    else scope.order(:id)
    end
  end
end
```

---

## 7. Factory Pattern (FactoryBot)

### Structure

```ruby
# frozen_string_literal: true

FactoryBot.define do
  factory :model_name do
    # Required associations
    association_name

    # Attributes with Faker
    name { Faker::Name.name }
    sequence(:email) { |n| "user#{n}@example.com" }
    status { :active }

    # Traits for variations
    trait :inactive do
      status { :inactive }
    end

    trait :with_associations do
      after(:create) do |record|
        create_list(:child, 3, parent: record)
      end
    end
  end
end
```

### Factory Rules

- One factory per file in `spec/factories/`
- Use `sequence` for unique attributes
- Use `Faker` for realistic data
- Use `trait` for common variations
- Use `after(:create)` for associated records
- Minimal defaults; traits add complexity
