# Ruby Code Patterns

Reference patterns for generic Ruby development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Service Object Pattern

Services encapsulate business logic in single-responsibility classes.

```ruby
# frozen_string_literal: true

module Users
  # Registers a new user and sends a welcome notification.
  #
  # @example
  #   Users::RegistrationService.new(email:, name:).call
  class RegistrationService
    # @param email [String] user email address
    # @param name [String] user display name
    def initialize(email:, name:)
      @email = email
      @name = name
    end

    # Executes the registration.
    #
    # @return [User] the created user
    # @raise [Errors::ValidationError] if input is invalid
    def call
      validate_input!
      user = create_user
      send_welcome(user)
      user
    end

    private

    attr_reader :email, :name

    def validate_input!
      errors = []
      errors << 'Email is required' if email.nil? || email.empty?
      errors << 'Name is required' if name.nil? || name.empty?
      raise Errors::ValidationError, errors unless errors.empty?
    end

    def create_user
      User.create(email:, name:)
    end

    def send_welcome(user)
      Notifications::WelcomeService.new(user:).call
    end
  end
end
```

### Service Rules

- Namespace under a module matching the domain
- Keyword arguments in `initialize`
- Single public `call` method
- Guard clauses and validation at the top
- Private `attr_reader` for instance variables
- Small private helpers for each step
- Raise domain-specific exceptions

---

## 2. Error Handling Pattern

Custom error hierarchy for domain-specific exceptions.

```ruby
# frozen_string_literal: true

module Errors
  # Base application error with error code support.
  class ApplicationError < StandardError
    attr_reader :code

    def initialize(message = nil, code: :internal_error)
      @code = code
      super(message)
    end
  end

  class NotFoundError < ApplicationError
    def initialize(resource, id)
      super("#{resource} not found: #{id}", code: :not_found)
    end
  end

  class ValidationError < ApplicationError
    def initialize(errors)
      super(Array(errors).join(', '), code: :validation_failed)
    end
  end

  class AuthorizationError < ApplicationError
    def initialize(message = 'Not authorized')
      super(message, code: :unauthorized)
    end
  end
end
```

### Error Handling Rules

- Inherit from a base `ApplicationError`
- Include error codes for programmatic handling
- Rescue specific exceptions, never bare `rescue`
- Log errors with context
- Return meaningful error messages

---

## 3. Logging Pattern

Structured logging with context.

```ruby
# frozen_string_literal: true

require 'logger'

module AppLogger
  module_function

  def logger
    @logger ||= Logger.new($stdout).tap do |l|
      l.formatter = proc do |severity, datetime, _progname, msg|
        "#{datetime.iso8601} #{severity}: #{msg}\n"
      end
    end
  end

  def info(message, **context)
    logger.info(format_message(message, context))
  end

  def error(message, **context)
    logger.error(format_message(message, context))
  end

  def format_message(message, context)
    return message if context.empty?

    "#{message} #{context.map { |k, v| "#{k}=#{v}" }.join(' ')}"
  end
end
```

---

## 4. Configuration Pattern

Environment-based configuration with sensible defaults.

```ruby
# frozen_string_literal: true

require 'yaml'

module Config
  module_function

  def database_url
    ENV.fetch('DATABASE_URL', 'postgres://localhost/myapp_development')
  end

  def redis_url
    ENV.fetch('REDIS_URL', 'redis://localhost:6379/0')
  end

  def env
    ENV.fetch('APP_ENV', 'development')
  end

  def production?
    env == 'production'
  end

  def test?
    env == 'test'
  end
end
```

---

## 5. Testing Patterns

### Unit Test

```ruby
# frozen_string_literal: true

require 'spec_helper'

RSpec.describe Users::RegistrationService do
  describe '#call' do
    subject(:service) { described_class.new(email:, name:) }

    let(:email) { 'user@example.com' }
    let(:name) { 'Test User' }

    context 'when input is valid' do
      it 'creates a user' do
        expect { service.call }.to change(User, :count).by(1)
      end

      it 'returns the created user' do
        result = service.call
        expect(result).to be_a(User)
        expect(result.email).to eq(email)
      end
    end

    context 'when email is missing' do
      let(:email) { nil }

      it 'raises ValidationError' do
        expect { service.call }.to raise_error(Errors::ValidationError)
      end
    end
  end
end
```

### Factory Pattern

```ruby
# frozen_string_literal: true

FactoryBot.define do
  factory :user do
    sequence(:email) { |n| "user#{n}@example.com" }
    name { 'Test User' }

    trait :admin do
      role { 'admin' }
    end

    trait :inactive do
      active { false }
    end
  end
end
```

### Test Rules

- One assertion focus per `it` block
- Use `let` for lazy-loaded data, `let!` only when eager loading needed
- Use `subject` for the thing under test
- Use `context` blocks starting with "when" or "with"
- Use `described_class` instead of repeating class name
- Test behavior, not implementation
- Use factories, never fixtures

---

## 6. Repository / Query Object Pattern

Encapsulate complex queries in dedicated classes.

```ruby
# frozen_string_literal: true

module Queries
  # Finds users matching search criteria with pagination.
  class UserSearch
    DEFAULT_PER_PAGE = 25

    # @param dataset [Sequel::Dataset] base dataset to query
    def initialize(dataset: User.dataset)
      @dataset = dataset
    end

    # @param query [String, nil] search term
    # @param page [Integer] page number
    # @param per_page [Integer] results per page
    # @return [Array<User>] matching users
    def call(query: nil, page: 1, per_page: DEFAULT_PER_PAGE)
      result = dataset
      result = result.where(Sequel.ilike(:name, "%#{query}%")) if query
      result = result.order(:name)
      result.paginate(page, per_page).all
    end

    private

    attr_reader :dataset
  end
end
```
