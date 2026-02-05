# GoodJob Patterns

## Overview

GoodJob is a Postgres-backed job processor. No Redis required - uses your existing database.

## Configuration

```ruby
# config/application.rb
config.active_job.queue_adapter = :good_job

# config/initializers/good_job.rb
GoodJob.active_record_parent_class = 'ApplicationRecord'
GoodJob.preserve_job_records = true
GoodJob.retry_on_unhandled_error = false
GoodJob.on_thread_error = -> (exception) { Rails.logger.error(exception) }
```

## Job Structure

Use standard ActiveJob:

```ruby
# app/jobs/process_order_job.rb
class ProcessOrderJob < ApplicationJob
  queue_as :default
  retry_on StandardError, wait: :polynomially_longer, attempts: 3

  def perform(order_id)
    order = Order.find(order_id)
    OrderProcessor.new(order).process!
  end
end
```

## Enqueuing Jobs

```ruby
# Immediate
ProcessOrderJob.perform_later(order.id)

# Delayed
ProcessOrderJob.set(wait: 5.minutes).perform_later(order.id)
ProcessOrderJob.set(wait_until: 1.hour.from_now).perform_later(order.id)
```

## Cron Jobs

```ruby
# config/initializers/good_job.rb
GoodJob::Cron.add('daily_cleanup', cron: '0 0 * * *', class: 'DailyCleanupJob')
GoodJob::Cron.add('hourly_sync', cron: '0 * * * *', class: 'HourlySyncJob')
```

## Dashboard

Mount the dashboard in routes:

```ruby
# config/routes.rb
mount GoodJob::Engine => '/good_job'
```

## Best Practices

1. **Use ActiveJob interface** - Standard Rails jobs work out of the box
2. **Leverage Postgres features** - SKIP LOCKED for efficient polling
3. **Enable dashboard** - Built-in web UI for monitoring
4. **Use cron for recurring** - No need for separate scheduler
5. **Keep job records** - Useful for debugging and auditing

## Testing

```ruby
# spec/jobs/process_order_job_spec.rb
require 'rails_helper'

RSpec.describe ProcessOrderJob do
  include ActiveJob::TestHelper

  it 'enqueues the job' do
    expect {
      ProcessOrderJob.perform_later(1)
    }.to have_enqueued_job(ProcessOrderJob).with(1)
  end

  it 'processes the order' do
    order = create(:order)
    perform_enqueued_jobs do
      ProcessOrderJob.perform_later(order.id)
    end
    expect(order.reload).to be_processed
  end
end
```
