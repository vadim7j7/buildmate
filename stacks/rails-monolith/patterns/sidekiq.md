# Sidekiq Job Patterns

## Overview

Sidekiq uses Redis for job queuing. It's the most popular Ruby background job processor.

## Job Structure

```ruby
# app/jobs/process_order_job.rb
class ProcessOrderJob
  include Sidekiq::Job

  sidekiq_options queue: :default, retry: 3

  def perform(order_id)
    order = Order.find(order_id)
    OrderProcessor.new(order).process!
  end
end
```

## Queue Configuration

```ruby
# config/sidekiq.yml
:concurrency: 5
:queues:
  - [critical, 3]
  - [default, 2]
  - [low, 1]
```

## Enqueuing Jobs

```ruby
# Immediate
ProcessOrderJob.perform_async(order.id)

# Delayed
ProcessOrderJob.perform_in(5.minutes, order.id)
ProcessOrderJob.perform_at(1.hour.from_now, order.id)

# Bulk
Sidekiq::Client.push_bulk(
  'class' => ProcessOrderJob,
  'args' => order_ids.map { |id| [id] }
)
```

## Best Practices

1. **Pass IDs, not objects** - Serialize only primitive types
2. **Make jobs idempotent** - Safe to retry
3. **Keep jobs small** - Under 30 seconds ideally
4. **Use appropriate queues** - Critical vs default vs low priority
5. **Handle errors gracefully** - Use `sidekiq_retries_exhausted`

## Error Handling

```ruby
class ProcessOrderJob
  include Sidekiq::Job

  sidekiq_retries_exhausted do |msg, ex|
    Sidekiq.logger.warn "Failed #{msg['class']} with #{msg['args']}: #{ex.message}"
    # Send to dead letter queue or alert
  end

  def perform(order_id)
    # ...
  end
end
```

## Testing

```ruby
# spec/jobs/process_order_job_spec.rb
require 'rails_helper'
require 'sidekiq/testing'

RSpec.describe ProcessOrderJob do
  before { Sidekiq::Testing.fake! }

  it 'enqueues the job' do
    expect {
      ProcessOrderJob.perform_async(1)
    }.to change(ProcessOrderJob.jobs, :size).by(1)
  end

  it 'processes the order' do
    Sidekiq::Testing.inline! do
      order = create(:order)
      ProcessOrderJob.perform_async(order.id)
      expect(order.reload).to be_processed
    end
  end
end
```
