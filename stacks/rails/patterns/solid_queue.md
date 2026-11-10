# SolidQueue Patterns

## Overview

SolidQueue is Rails 8's default database-backed job processor. Built by 37signals for Hey.

## Configuration

New Rails 8 apps come with Solid Queue installed. For an older app:
`bundle add solid_queue && bin/rails solid_queue:install`.

```ruby
# config/environments/production.rb (generated)
config.active_job.queue_adapter = :solid_queue
config.solid_queue.connects_to = { database: { writing: :queue } }
```

```yaml
# config/database.yml: production has a separate queue database
production:
  primary: { <<: *default, database: app_production }
  queue:   { <<: *default, database: app_production_queue, migrations_paths: db/queue_migrate }

# config/queue.yml
default: &default
  dispatchers:
    - polling_interval: 1
      batch_size: 500
  workers:
    - queues: "*"
      threads: 3
      processes: <%= ENV.fetch("JOB_CONCURRENCY", 1) %>
      polling_interval: 0.1
```

- The queue schema lives in `db/queue_schema.rb`, not in `db/migrate/`.
- Run workers with `bin/jobs`, or inside Puma with `SOLID_QUEUE_IN_PUMA=true`
  (the `plugin :solid_queue` line in `config/puma.rb`), the usual single-server
  Kamal setup.
- In development the generated config uses `:async` unless you opt in; check
  `config/environments/development.rb` before assuming jobs hit the queue DB.

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

## Long Jobs: Continuations (Rails 8.1+)

A job that walks many records should survive a deploy restart without starting
over. `ActiveJob::Continuable` splits `perform` into steps; on shutdown the job
stops at the next checkpoint and is re-enqueued, resuming from the saved cursor.
Use it only when the app is on Rails 8.1 or later (check `Gemfile.lock`).

```ruby
class BackfillScoresJob < ApplicationJob
  include ActiveJob::Continuable

  def perform(import_id)
    @import = Import.find(import_id)

    step :prepare do
      @import.update!(status: :running)
    end

    step :process do |step|
      @import.records.find_each(start: step.cursor) do |record|
        record.recalculate_score!
        step.advance! from: record.id   # saves the cursor and checkpoints
      end
    end

    step :finish   # calls the private method of the same name
  end

  private

  def finish
    @import.update!(status: :done)
  end
end
```

Each step must be safe to re-run from its cursor (idempotent writes).

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
