# SolidQueue Patterns

## Overview

SolidQueue is Rails 8's default database-backed job processor. Built by 37signals for Hey.

## Configuration

```ruby
# config/application.rb
config.active_job.queue_adapter = :solid_queue

# config/solid_queue.yml
production:
  dispatchers:
    - polling_interval: 1
      batch_size: 500
  workers:
    - queues: "*"
      threads: 5
      polling_interval: 0.1
```

## Job Structure

Use standard ActiveJob:

```ruby
# app/jobs/process_order_job.rb
class ProcessOrderJob < ApplicationJob
  queue_as :default
  limits_concurrency to: 1, key: ->(order_id) { order_id }

  def perform(order_id)
    order = Order.find(order_id)
    OrderProcessor.new(order).process!
  end
end
```

## Concurrency Control

SolidQueue has built-in concurrency limiting:

```ruby
class ImportJob < ApplicationJob
  # Only 2 imports at a time globally
  limits_concurrency to: 2

  def perform(import_id)
    # ...
  end
end

class UserSyncJob < ApplicationJob
  # Only 1 sync per user at a time
  limits_concurrency to: 1, key: ->(user_id) { user_id }

  def perform(user_id)
    # ...
  end
end
```

## Recurring Jobs

```ruby
# config/recurring.yml
production:
  daily_cleanup:
    class: DailyCleanupJob
    schedule: every day at 2am
  hourly_sync:
    class: HourlySyncJob
    schedule: every hour
```

## Best Practices

1. **Use concurrency controls** - Prevent thundering herd
2. **Leverage database transactions** - Jobs and data in same DB
3. **Configure workers per queue** - Different throughput needs
4. **Use recurring jobs** - Built-in scheduling
5. **Monitor with Mission Control** - 37signals' monitoring gem

## Mission Control

```ruby
# Gemfile
gem 'mission_control-jobs'

# config/routes.rb
mount MissionControl::Jobs::Engine, at: '/jobs'
```

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

  it 'processes the order inline' do
    order = create(:order)
    perform_enqueued_jobs do
      ProcessOrderJob.perform_later(order.id)
    end
    expect(order.reload).to be_processed
  end
end
```
