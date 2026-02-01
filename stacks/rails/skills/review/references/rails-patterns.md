# Rails Code Pattern References

Canonical code patterns for the Rails backend. The reviewer agent uses these as the
reference standard when evaluating code changes.

---

## 1. Service Pattern

Services encapsulate business logic. They are namespaced under modules, inherit from
`ApplicationService`, accept keyword arguments, and expose a single `call` method.

```ruby
# frozen_string_literal: true

module BulkImport
  # Imports profiles from a CSV file, creating or updating records.
  #
  # @example
  #   BulkImport::ProfilesService.new(file:, user:).call
  class ProfilesService < ApplicationService
    # @param file [ActionDispatch::Http::UploadedFile] the CSV file
    # @param user [User] the user performing the import
    def initialize(file:, user:)
      @file = file
      @user = user
    end

    # @return [Result] import result with counts and errors
    def call
      return Result.failure('File is empty') if file_empty?

      process_rows
      Result.success(imported_count:, errors:)
    end

    private

    attr_reader :file, :user

    def file_empty?
      CSV.read(file.path).size <= 1
    end

    def process_rows
      CSV.foreach(file.path, headers: true) do |row|
        import_row(row)
      rescue StandardError => e
        errors << "Row #{row.index}: #{e.message}"
      end
    end

    def import_row(row)
      profile = Profile.find_or_initialize_by(email: row['email'])
      profile.assign_attributes(name: row['name'], bio: row['bio'], imported_by: user)
      profile.save!
      @imported_count += 1
    end

    def imported_count
      @imported_count ||= 0
    end

    def errors
      @errors ||= []
    end
  end
end
```

### ApplicationService Base Class

```ruby
# frozen_string_literal: true

# Base class for all service objects.
class ApplicationService
  def self.call(...)
    new(...).call
  end
end
```

---

## 2. Presenter Pattern

Presenters serialize model data for API responses. They inherit from `BasePresenter`
and expose a `call` method that returns a hash.

```ruby
# frozen_string_literal: true

# Presents profile data for API responses.
#
# @example
#   ProfilePresenter.new(profile).call
#   ProfilePresenter.new(profiles).call  # handles collections
class ProfilePresenter < BasePresenter
  # @return [Hash, Array<Hash>] serialized profile data
  def call
    if record.respond_to?(:each)
      record.map { |r| present_one(r) }
    else
      present_one(record)
    end
  end

  private

  def present_one(profile)
    {
      id: profile.id,
      name: profile.name,
      email: profile.email,
      bio: profile.bio,
      company: company_data(profile),
      skills: profile.skills.pluck(:name),
      active: profile.active,
      created_at: profile.created_at.iso8601,
      updated_at: profile.updated_at.iso8601
    }
  end

  def company_data(profile)
    return unless profile.company

    {
      id: profile.company.id,
      name: profile.company.name,
      domain: profile.company.domain
    }
  end
end
```

### BasePresenter

```ruby
# frozen_string_literal: true

# Base class for all presenters.
class BasePresenter
  attr_reader :record

  # @param record [ApplicationRecord, ActiveRecord::Relation] the record(s) to present
  def initialize(record)
    @record = record
  end

  def call
    raise NotImplementedError, "#{self.class}#call must be implemented"
  end
end
```

---

## 3. Controller Pattern

Controllers are RESTful, use strong params, extract shared logic into concerns,
and use presenters for response serialization.

```ruby
# frozen_string_literal: true

module Api
  module V1
    # Manages candidate profile CRUD operations.
    class ProfilesController < BaseController
      before_action :authenticate_user!
      before_action :set_profile, only: %i[show update destroy]

      # GET /api/v1/profiles
      #
      # @return [JSON] paginated list of profiles
      def index
        profiles = current_user.profiles
          .includes(:company, :skills)
          .search(params[:q])
          .page(params[:page])
          .per(params[:per_page] || 25)

        render json: {
          profiles: ProfilePresenter.new(profiles).call,
          meta: pagination_meta(profiles)
        }
      end

      # GET /api/v1/profiles/:id
      def show
        render json: ProfilePresenter.new(@profile).call
      end

      # POST /api/v1/profiles
      def create
        profile = current_user.profiles.build(profile_params)

        if profile.save
          render json: ProfilePresenter.new(profile).call, status: :created
        else
          render_validation_errors(profile)
        end
      end

      # PATCH /api/v1/profiles/:id
      def update
        if @profile.update(profile_params)
          render json: ProfilePresenter.new(@profile).call
        else
          render_validation_errors(@profile)
        end
      end

      # DELETE /api/v1/profiles/:id
      def destroy
        @profile.destroy!
        head :no_content
      end

      private

      def set_profile
        @profile = current_user.profiles.find(params[:id])
      end

      def profile_params
        params.require(:profile).permit(:name, :email, :bio, :company_id)
      end
    end
  end
end
```

### Controller Concern Example

```ruby
# frozen_string_literal: true

module Paginatable
  extend ActiveSupport::Concern

  private

  # @param collection [ActiveRecord::Relation] paginated collection
  # @return [Hash] pagination metadata
  def pagination_meta(collection)
    {
      current_page: collection.current_page,
      total_pages: collection.total_pages,
      total_count: collection.total_count,
      per_page: collection.limit_value
    }
  end
end
```

---

## 4. Model Associations and Scopes

Models follow a consistent ordering: associations, validations, enums, scopes,
callbacks, then methods.

```ruby
# frozen_string_literal: true

class Profile < ApplicationRecord
  # -- Associations --
  belongs_to :user
  belongs_to :company, optional: true
  has_many :experiences, dependent: :destroy
  has_many :profile_skills, dependent: :destroy
  has_many :skills, through: :profile_skills
  has_one :resume, dependent: :destroy
  has_paper_trail

  # -- Validations --
  validates :name, presence: true, length: { maximum: 255 }
  validates :email, presence: true, uniqueness: { case_sensitive: false }

  # -- Enums --
  enum :status, { active: 0, inactive: 1, archived: 2 }, default: :active

  # -- Scopes --
  scope :active, -> { where(status: :active) }
  scope :recent, -> { order(created_at: :desc) }
  scope :search, ->(query) {
    return all if query.blank?

    where('name ILIKE ? OR email ILIKE ?', "%#{query}%", "%#{query}%")
  }
  scope :with_associations, -> { includes(:company, :skills, :experiences) }

  # -- Callbacks --
  before_validation :normalize_email
  after_create_commit :send_welcome_notification

  # -- Public Methods --

  # @return [String] the full display name
  def display_name
    company ? "#{name} (#{company.name})" : name
  end

  private

  def normalize_email
    self.email = email&.strip&.downcase
  end

  def send_welcome_notification
    NotificationJob.perform_later(user_id: user.id, type: 'profile_created')
  end
end
```

---

## 5. Job Pattern with Sidekiq

Jobs are namespaced, configure queue and retry behavior, and delegate to services.

```ruby
# frozen_string_literal: true

module Sync
  # Syncs company data from external provider on a schedule.
  #
  # @example
  #   Sync::CompanyDataJob.perform_later(company_id: 123, provider: 'clearbit')
  class CompanyDataJob < ApplicationJob
    queue_as :low_priority
    sidekiq_options retry: 5, backtrace: true

    retry_on ActiveRecord::Deadlocked, wait: 5.seconds, attempts: 3
    discard_on ActiveJob::DeserializationError

    # @param company_id [Integer] the company to sync
    # @param provider [String] the data provider name
    def perform(company_id, provider = 'clearbit')
      company = Company.find(company_id)
      return if company.synced_recently?

      Sync::CompanyDataService.new(company:, provider:).call
    rescue ActiveRecord::RecordNotFound => e
      Rails.logger.warn("Company not found for sync: #{e.message}")
    end
  end
end
```

---

## 6. Query Object Pattern

For complex queries, extract into query objects that inherit from `ApplicationQuery`.

```ruby
# frozen_string_literal: true

# Searches profiles with filtering, sorting, and eager loading.
#
# @example
  #   Profiles::SearchQuery.new(params:, scope: current_user.profiles).call
class Profiles::SearchQuery < ApplicationQuery
  # @param params [ActionController::Parameters] search parameters
  # @param scope [ActiveRecord::Relation] base scope
  def initialize(params:, scope: Profile.all)
    @params = params
    @scope = scope
  end

  # @return [ActiveRecord::Relation] filtered and sorted profiles
  def call
    @scope
      .then { |s| filter_by_status(s) }
      .then { |s| filter_by_company(s) }
      .then { |s| search_by_name(s) }
      .then { |s| apply_sorting(s) }
      .includes(:company, :skills)
  end

  private

  attr_reader :params

  def filter_by_status(scope)
    return scope if params[:status].blank?

    scope.where(status: params[:status])
  end

  def filter_by_company(scope)
    return scope if params[:company_id].blank?

    scope.where(company_id: params[:company_id])
  end

  def search_by_name(scope)
    return scope if params[:q].blank?

    scope.where('name ILIKE ?', "%#{params[:q]}%")
  end

  def apply_sorting(scope)
    case params[:sort]
    when 'name' then scope.order(:name)
    when 'recent' then scope.order(created_at: :desc)
    else scope.order(:created_at)
    end
  end
end
```

---

## 7. Factory Pattern (FactoryBot)

```ruby
# frozen_string_literal: true

FactoryBot.define do
  factory :profile do
    user
    company

    name { Faker::Name.name }
    sequence(:email) { |n| "profile#{n}@example.com" }
    bio { Faker::Lorem.paragraph }
    status { :active }

    trait :inactive do
      status { :inactive }
    end

    trait :with_experiences do
      after(:create) do |profile|
        create_list(:experience, 3, profile:)
      end
    end
  end
end
```
