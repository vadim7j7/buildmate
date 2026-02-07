# Rails Error Tracking Patterns

Error tracking patterns using Sentry for Rails applications.

---

## 1. Sentry Setup

### Gemfile

```ruby
gem 'sentry-ruby'
gem 'sentry-rails'
gem 'sentry-sidekiq'  # If using Sidekiq
```

### Configuration

```ruby
# config/initializers/sentry.rb
Sentry.init do |config|
  config.dsn = ENV['SENTRY_DSN']
  config.environment = Rails.env
  config.release = ENV.fetch('GIT_SHA', 'development')

  # Breadcrumbs for debugging
  config.breadcrumbs_logger = [:active_support_logger, :http_logger]

  # Performance monitoring
  config.traces_sample_rate = Rails.env.production? ? 0.1 : 1.0
  config.profiles_sample_rate = 0.1

  # Filter sensitive data
  config.before_send = lambda do |event, hint|
    # Don't send events in development
    return nil if Rails.env.development?

    # Filter specific exceptions
    exception = hint[:exception]
    return nil if exception.is_a?(ActiveRecord::RecordNotFound)
    return nil if exception.is_a?(ActionController::RoutingError)

    event
  end

  # Add user context
  config.before_send_transaction = lambda do |event, hint|
    event
  end
end
```

---

## 2. User Context

```ruby
# app/controllers/application_controller.rb
class ApplicationController < ActionController::API
  before_action :set_sentry_context

  private

  def set_sentry_context
    return unless current_user

    Sentry.set_user(
      id: current_user.id,
      email: current_user.email,
      username: current_user.name,
      ip_address: request.remote_ip,
      subscription: current_user.subscription_plan
    )

    Sentry.set_tags(
      account_id: current_user.account_id,
      locale: I18n.locale
    )

    Sentry.set_extras(
      params: request.filtered_parameters,
      url: request.url
    )
  end
end
```

---

## 3. Custom Error Classes

```ruby
# app/errors/application_error.rb
class ApplicationError < StandardError
  attr_reader :code, :details, :severity

  def initialize(message = nil, code: nil, details: {}, severity: :error)
    @code = code
    @details = details
    @severity = severity
    super(message)
  end

  def sentry_context
    {
      code: code,
      details: details,
      severity: severity
    }
  end
end

# Specific error types
class ValidationError < ApplicationError
  def initialize(message, errors: {})
    super(message, code: 'VALIDATION_ERROR', details: { errors: errors })
  end
end

class BusinessLogicError < ApplicationError
  def initialize(message, code: 'BUSINESS_ERROR', **details)
    super(message, code: code, details: details)
  end
end

class ExternalServiceError < ApplicationError
  def initialize(service:, message:, response: nil)
    super(
      message,
      code: 'EXTERNAL_SERVICE_ERROR',
      details: { service: service, response: response }
    )
  end
end

class RateLimitError < ApplicationError
  def initialize(limit:, window:)
    super(
      "Rate limit exceeded",
      code: 'RATE_LIMIT_ERROR',
      details: { limit: limit, window: window },
      severity: :warning
    )
  end
end
```

---

## 4. Centralized Error Handling

```ruby
# app/controllers/concerns/error_handling.rb
module ErrorHandling
  extend ActiveSupport::Concern

  included do
    rescue_from StandardError, with: :handle_internal_error
    rescue_from ApplicationError, with: :handle_application_error
    rescue_from ActiveRecord::RecordNotFound, with: :handle_not_found
    rescue_from ActiveRecord::RecordInvalid, with: :handle_validation_error
    rescue_from ActionController::ParameterMissing, with: :handle_bad_request
    rescue_from Pundit::NotAuthorizedError, with: :handle_unauthorized
  end

  private

  def handle_application_error(exception)
    Sentry.set_extras(exception.sentry_context)

    case exception.severity
    when :warning
      Sentry.capture_message(exception.message, level: :warning)
    when :error
      Sentry.capture_exception(exception)
    end

    render_error(
      status: error_status_for(exception),
      code: exception.code,
      message: exception.message,
      details: exception.details
    )
  end

  def handle_internal_error(exception)
    Sentry.capture_exception(exception)

    render_error(
      status: :internal_server_error,
      code: 'INTERNAL_ERROR',
      message: Rails.env.production? ? 'An unexpected error occurred' : exception.message
    )
  end

  def handle_not_found(exception)
    render_error(
      status: :not_found,
      code: 'NOT_FOUND',
      message: "Resource not found"
    )
  end

  def handle_validation_error(exception)
    render_error(
      status: :unprocessable_entity,
      code: 'VALIDATION_ERROR',
      message: 'Validation failed',
      details: { errors: exception.record.errors.to_hash }
    )
  end

  def handle_bad_request(exception)
    render_error(
      status: :bad_request,
      code: 'BAD_REQUEST',
      message: exception.message
    )
  end

  def handle_unauthorized(exception)
    render_error(
      status: :forbidden,
      code: 'FORBIDDEN',
      message: 'You are not authorized to perform this action'
    )
  end

  def render_error(status:, code:, message:, details: {})
    render json: {
      error: {
        code: code,
        message: message,
        **details
      }
    }, status: status
  end

  def error_status_for(exception)
    case exception
    when ValidationError then :unprocessable_entity
    when RateLimitError then :too_many_requests
    when ExternalServiceError then :bad_gateway
    else :internal_server_error
    end
  end
end
```

---

## 5. Background Job Error Tracking

```ruby
# app/jobs/concerns/error_tracking.rb
module ErrorTracking
  extend ActiveSupport::Concern

  included do
    rescue_from StandardError, with: :handle_job_error
  end

  private

  def handle_job_error(exception)
    Sentry.set_tags(
      job_class: self.class.name,
      queue: queue_name,
      job_id: job_id
    )

    Sentry.set_extras(
      arguments: arguments,
      executions: executions,
      scheduled_at: scheduled_at
    )

    Sentry.capture_exception(exception)

    raise exception  # Re-raise for retry mechanism
  end
end

# Base job class
class ApplicationJob < ActiveJob::Base
  include ErrorTracking

  retry_on StandardError, wait: :exponentially_longer, attempts: 5
  discard_on ActiveJob::DeserializationError
end
```

---

## 6. Service Error Handling

```ruby
# app/services/concerns/error_handling.rb
module ServiceErrorHandling
  extend ActiveSupport::Concern

  private

  def capture_error(error, context: {})
    Sentry.set_extras(context)
    Sentry.capture_exception(error)
  end

  def with_error_handling(context: {})
    yield
  rescue ApplicationError
    raise  # Let application errors bubble up
  rescue StandardError => e
    capture_error(e, context: context)
    raise ExternalServiceError.new(
      service: self.class.name,
      message: e.message
    )
  end
end

# Usage
class PaymentService
  include ServiceErrorHandling

  def process_payment(order)
    with_error_handling(context: { order_id: order.id }) do
      gateway.charge(order.total, order.payment_method)
    end
  end
end
```

---

## 7. Transaction Monitoring

```ruby
# app/services/transaction_monitor.rb
class TransactionMonitor
  def self.track(operation_name, **tags)
    transaction = Sentry.start_transaction(
      op: operation_name,
      name: operation_name
    )

    Sentry.set_tags(tags)

    begin
      result = yield
      transaction.set_status('ok')
      result
    rescue StandardError => e
      transaction.set_status('internal_error')
      raise
    ensure
      transaction.finish
    end
  end
end

# Usage
class OrderService
  def create_order(params)
    TransactionMonitor.track('order.create', user_id: current_user.id) do
      Order.create!(params)
    end
  end
end
```

---

## 8. Custom Spans

```ruby
# app/services/order_processor.rb
class OrderProcessor
  def process(order)
    parent_span = Sentry.get_current_scope.get_span

    # Validate order
    child_span = parent_span.start_child(op: 'validation', description: 'Validate order')
    validate_order(order)
    child_span.finish

    # Process payment
    child_span = parent_span.start_child(op: 'payment', description: 'Process payment')
    process_payment(order)
    child_span.finish

    # Send notifications
    child_span = parent_span.start_child(op: 'notification', description: 'Send notifications')
    send_notifications(order)
    child_span.finish
  end
end
```

---

## 9. Error Fingerprinting

```ruby
# config/initializers/sentry.rb
Sentry.init do |config|
  # ...

  config.before_send = lambda do |event, hint|
    exception = hint[:exception]

    # Custom fingerprinting for specific errors
    if exception.is_a?(ExternalServiceError)
      event.fingerprint = ['external-service', exception.details[:service]]
    end

    if exception.is_a?(ActiveRecord::ConnectionNotEstablished)
      event.fingerprint = ['database-connection-error']
    end

    event
  end
end
```

---

## 10. Health Check Integration

```ruby
# app/controllers/health_controller.rb
class HealthController < ApplicationController
  skip_before_action :authenticate!

  def show
    checks = {
      database: check_database,
      redis: check_redis,
      sidekiq: check_sidekiq
    }

    healthy = checks.values.all? { |c| c[:status] == 'ok' }

    unless healthy
      Sentry.capture_message(
        'Health check failed',
        level: :warning,
        extra: { checks: checks }
      )
    end

    render json: {
      status: healthy ? 'healthy' : 'degraded',
      checks: checks
    }, status: healthy ? :ok : :service_unavailable
  end

  private

  def check_database
    ActiveRecord::Base.connection.execute('SELECT 1')
    { status: 'ok' }
  rescue StandardError => e
    { status: 'error', message: e.message }
  end

  def check_redis
    Redis.current.ping
    { status: 'ok' }
  rescue StandardError => e
    { status: 'error', message: e.message }
  end

  def check_sidekiq
    stats = Sidekiq::Stats.new
    {
      status: 'ok',
      queues: stats.queues,
      enqueued: stats.enqueued
    }
  rescue StandardError => e
    { status: 'error', message: e.message }
  end
end
```

---

## 11. Alert Configuration

```ruby
# lib/tasks/sentry.rake
namespace :sentry do
  desc 'Test Sentry configuration'
  task test: :environment do
    begin
      raise 'Test Sentry error - please ignore'
    rescue => e
      Sentry.capture_exception(e)
      puts 'Sentry test event sent!'
    end
  end
end
```

---

## 12. Release Tracking

```ruby
# config/initializers/sentry.rb
Sentry.init do |config|
  config.release = if ENV['HEROKU_SLUG_COMMIT']
    ENV['HEROKU_SLUG_COMMIT']
  elsif ENV['GIT_SHA']
    ENV['GIT_SHA']
  else
    `git rev-parse HEAD`.strip rescue 'unknown'
  end

  # Associate commits with releases
  config.send_default_pii = false
  config.attach_stacktrace = true
end
```
