# Rails Structured Logging Patterns

Structured logging patterns using Rails.logger and Lograge.

---

## 1. Lograge Setup

### Gemfile

```ruby
gem 'lograge'
gem 'lograge-sql'  # Optional: SQL query logging
```

### Configuration

```ruby
# config/initializers/lograge.rb
Rails.application.configure do
  config.lograge.enabled = true
  config.lograge.formatter = Lograge::Formatters::Json.new

  # Keep original Rails logs in development
  config.lograge.keep_original_rails_log = Rails.env.development?

  # Add custom data to every request
  config.lograge.custom_options = lambda do |event|
    {
      host: event.payload[:host],
      request_id: event.payload[:request_id],
      user_id: event.payload[:user_id],
      ip: event.payload[:ip],
      user_agent: event.payload[:user_agent],
      time: Time.current.iso8601,
      params: event.payload[:params].except(*%w[controller action format])
    }
  end

  # Add custom payload data
  config.lograge.custom_payload do |controller|
    {
      host: controller.request.host,
      request_id: controller.request.request_id,
      user_id: controller.current_user&.id,
      ip: controller.request.remote_ip,
      user_agent: controller.request.user_agent
    }
  end
end
```

---

## 2. Tagged Logging

```ruby
# config/application.rb
config.log_tags = [
  :request_id,
  ->(request) { request.session[:user_id] },
  ->(request) { request.env['HTTP_X_CORRELATION_ID'] }
]

# Controller usage
class ApplicationController < ActionController::API
  around_action :tag_logs

  private

  def tag_logs
    Rails.logger.tagged(
      "user:#{current_user&.id}",
      "request:#{request.request_id}"
    ) do
      yield
    end
  end
end
```

---

## 3. Structured Logger Service

```ruby
# app/services/structured_logger.rb
class StructuredLogger
  LEVELS = %i[debug info warn error fatal].freeze

  def initialize(context = {})
    @context = context
    @logger = Rails.logger
  end

  LEVELS.each do |level|
    define_method(level) do |message, **extra|
      log(level, message, **extra)
    end
  end

  def with_context(**new_context)
    self.class.new(@context.merge(new_context))
  end

  def log(level, message, **extra)
    payload = build_payload(message, extra)
    @logger.public_send(level, payload.to_json)
  end

  private

  def build_payload(message, extra)
    {
      message: message,
      timestamp: Time.current.iso8601,
      level: level.to_s.upcase,
      **@context,
      **extra
    }
  end
end

# Usage in services
class OrderService
  def initialize
    @logger = StructuredLogger.new(service: 'OrderService')
  end

  def create_order(user, params)
    @logger.info('Creating order', user_id: user.id, params: params)

    order = Order.create!(params.merge(user: user))

    @logger.info('Order created', order_id: order.id, total: order.total)
    order
  rescue StandardError => e
    @logger.error('Order creation failed',
      error: e.message,
      backtrace: e.backtrace.first(5)
    )
    raise
  end
end
```

---

## 4. Request Logging Middleware

```ruby
# app/middleware/request_logger.rb
class RequestLogger
  def initialize(app)
    @app = app
    @logger = StructuredLogger.new(component: 'http')
  end

  def call(env)
    request = ActionDispatch::Request.new(env)
    start_time = Process.clock_gettime(Process::CLOCK_MONOTONIC)

    @logger.info('Request started',
      method: request.request_method,
      path: request.path,
      request_id: request.request_id
    )

    status, headers, response = @app.call(env)

    duration = ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - start_time) * 1000).round(2)

    @logger.info('Request completed',
      method: request.request_method,
      path: request.path,
      status: status,
      duration_ms: duration,
      request_id: request.request_id
    )

    [status, headers, response]
  rescue StandardError => e
    duration = ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - start_time) * 1000).round(2)

    @logger.error('Request failed',
      method: request.request_method,
      path: request.path,
      error: e.message,
      duration_ms: duration,
      request_id: request.request_id
    )

    raise
  end
end

# config/application.rb
config.middleware.insert_before Rails::Rack::Logger, RequestLogger
```

---

## 5. Job Logging

```ruby
# app/jobs/concerns/job_logging.rb
module JobLogging
  extend ActiveSupport::Concern

  included do
    around_perform :log_job_execution
  end

  private

  def log_job_execution(job)
    logger = StructuredLogger.new(
      component: 'job',
      job_class: self.class.name,
      job_id: job.job_id,
      queue: job.queue_name
    )

    start_time = Process.clock_gettime(Process::CLOCK_MONOTONIC)
    logger.info('Job started', arguments: job.arguments)

    yield

    duration = ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - start_time) * 1000).round(2)
    logger.info('Job completed', duration_ms: duration)
  rescue StandardError => e
    duration = ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - start_time) * 1000).round(2)
    logger.error('Job failed',
      error: e.message,
      backtrace: e.backtrace.first(10),
      duration_ms: duration
    )
    raise
  end
end

# Usage
class ProcessOrderJob < ApplicationJob
  include JobLogging

  def perform(order_id)
    # Job logic
  end
end
```

---

## 6. Database Query Logging

```ruby
# config/initializers/sql_logging.rb
if Rails.env.production?
  ActiveSupport::Notifications.subscribe('sql.active_record') do |*args|
    event = ActiveSupport::Notifications::Event.new(*args)

    # Only log slow queries in production
    next unless event.duration > 100 # milliseconds

    Rails.logger.warn({
      message: 'Slow query detected',
      component: 'database',
      query: event.payload[:sql].truncate(1000),
      duration_ms: event.duration.round(2),
      name: event.payload[:name],
      cached: event.payload[:cached]
    }.to_json)
  end
end
```

---

## 7. Log Levels by Environment

```ruby
# config/environments/development.rb
config.log_level = :debug
config.lograge.enabled = false

# config/environments/production.rb
config.log_level = ENV.fetch('LOG_LEVEL', 'info').to_sym
config.lograge.enabled = true

# config/environments/test.rb
config.log_level = :warn
```

---

## 8. Log Filtering

```ruby
# config/initializers/filter_parameter_logging.rb
Rails.application.config.filter_parameters += [
  :password,
  :password_confirmation,
  :token,
  :api_key,
  :secret,
  :credit_card,
  :ssn,
  /authorization/i,
  /bearer/i
]

# Custom log filter for sensitive data
class SensitiveDataFilter
  PATTERNS = [
    /\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}/, # Credit card
    /\d{3}-\d{2}-\d{4}/, # SSN
  ].freeze

  def self.filter(message)
    PATTERNS.reduce(message.to_s) do |msg, pattern|
      msg.gsub(pattern, '[FILTERED]')
    end
  end
end
```

---

## 9. Correlation IDs

```ruby
# app/controllers/concerns/correlation_tracking.rb
module CorrelationTracking
  extend ActiveSupport::Concern

  included do
    before_action :set_correlation_id
  end

  private

  def set_correlation_id
    @correlation_id = request.headers['X-Correlation-ID'] || SecureRandom.uuid
    response.headers['X-Correlation-ID'] = @correlation_id
    Current.correlation_id = @correlation_id
  end
end

# app/models/current.rb
class Current < ActiveSupport::CurrentAttributes
  attribute :correlation_id, :user, :request_id
end

# Use in services
class StructuredLogger
  def build_payload(message, extra)
    {
      message: message,
      timestamp: Time.current.iso8601,
      correlation_id: Current.correlation_id,
      request_id: Current.request_id,
      **@context,
      **extra
    }
  end
end
```

---

## 10. External Service Logging

```ruby
# app/services/concerns/external_service_logging.rb
module ExternalServiceLogging
  extend ActiveSupport::Concern

  private

  def log_external_request(service_name, method, url, &block)
    logger = StructuredLogger.new(
      component: 'external_service',
      service: service_name,
      correlation_id: Current.correlation_id
    )

    start_time = Process.clock_gettime(Process::CLOCK_MONOTONIC)
    logger.info('External request started', method: method, url: url)

    result = yield

    duration = ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - start_time) * 1000).round(2)
    logger.info('External request completed',
      method: method,
      url: url,
      status: result.status,
      duration_ms: duration
    )

    result
  rescue StandardError => e
    duration = ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - start_time) * 1000).round(2)
    logger.error('External request failed',
      method: method,
      url: url,
      error: e.message,
      duration_ms: duration
    )
    raise
  end
end

# Usage
class StripeService
  include ExternalServiceLogging

  def create_charge(amount, customer_id)
    log_external_request('stripe', 'POST', '/v1/charges') do
      Stripe::Charge.create(amount: amount, customer: customer_id)
    end
  end
end
```

---

## 11. Log Output Destinations

```ruby
# config/initializers/logging.rb
Rails.application.configure do
  if ENV['LOG_TO_STDOUT'].present?
    # Container/cloud logging
    logger = ActiveSupport::Logger.new(STDOUT)
    logger.formatter = proc do |severity, datetime, progname, msg|
      "#{msg}\n"
    end
    config.logger = ActiveSupport::TaggedLogging.new(logger)
  end

  # Optional: Send to external service
  if ENV['LOGTAIL_TOKEN'].present?
    require 'logtail'
    config.logger = Logtail::Logger.create_from_source(ENV['LOGTAIL_TOKEN'])
  end
end
```
