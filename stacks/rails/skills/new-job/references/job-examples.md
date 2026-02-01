# Sidekiq Job Examples

Production-ready background job examples demonstrating queue configuration, retry
behavior, error handling, and service delegation.

---

## Example 1: Data Sync Job

```ruby
# frozen_string_literal: true

module Sync
  # Imports data from Airtable for a specific import record.
  # Delegates to Sync::AirtableImportService for the actual import logic.
  #
  # @example
  #   Sync::AirtableImportJob.perform_later(import.id)
  class AirtableImportJob < ApplicationJob
    queue_as :default
    sidekiq_options retry: 3, backtrace: true

    retry_on ActiveRecord::Deadlocked, wait: 5.seconds, attempts: 3
    retry_on Faraday::TimeoutError, wait: :polynomially_longer, attempts: 5
    discard_on ActiveJob::DeserializationError

    # @param import_id [Integer] the Import record ID to process
    def perform(import_id)
      import = Import.find(import_id)
      return if import.completed?

      import.start!
      result = Sync::AirtableImportService.new(import:).call

      if result.success?
        import.complete!(imported_count: result.imported_count, error_count: result.error_count)
      else
        import.update!(status: :failed, error_messages: result.errors)
      end
    rescue ActiveRecord::RecordNotFound => e
      Rails.logger.warn("Import record not found: #{e.message}")
    end
  end
end
```

---

## Example 2: Notification Job

```ruby
# frozen_string_literal: true

module Notifications
  # Sends a notification to a user via their preferred channel.
  #
  # @example
  #   Notifications::SendJob.perform_later(user_id: 1, type: 'welcome')
  #   Notifications::SendJob.perform_later(user_id: 1, type: 'profile_viewed', metadata: { viewer_id: 2 })
  class SendJob < ApplicationJob
    queue_as :notifications
    sidekiq_options retry: 2

    discard_on ActiveRecord::RecordNotFound

    # @param user_id [Integer] the user to notify
    # @param type [String] the notification type
    # @param metadata [Hash] additional notification context
    def perform(user_id:, type:, metadata: {})
      user = User.find(user_id)
      return unless user.notifications_enabled?

      Notifications::DeliveryService.new(
        user:,
        type:,
        metadata:
      ).call
    end
  end
end
```

---

## Example 3: Batch Processing Job

```ruby
# frozen_string_literal: true

module Maintenance
  # Processes stale profiles in batches, archiving those inactive for 90+ days.
  # Designed to run on a schedule via Sidekiq-Cron.
  #
  # @example
  #   Maintenance::ArchiveStaleProfilesJob.perform_later
  class ArchiveStaleProfilesJob < ApplicationJob
    queue_as :low_priority
    sidekiq_options retry: 1, lock: :until_executed

    BATCH_SIZE = 500
    STALE_THRESHOLD = 90.days

    # Finds and archives profiles that have been inactive for over 90 days.
    def perform
      stale_profiles = Profile
        .active
        .where('last_active_at < ?', STALE_THRESHOLD.ago)

      stale_profiles.find_in_batches(batch_size: BATCH_SIZE) do |batch|
        Profile.where(id: batch.map(&:id)).update_all(
          status: :archived,
          archived_at: Time.current
        )

        Rails.logger.info("Archived #{batch.size} stale profiles")
      end

      Rails.logger.info(
        "Archive job complete: #{stale_profiles.count} profiles archived"
      )
    end
  end
end
```

---

## Example 4: Job with External API Call

```ruby
# frozen_string_literal: true

module Enrichment
  # Enriches company data by fetching information from Clearbit.
  # Handles rate limiting by re-scheduling with exponential backoff.
  #
  # @example
  #   Enrichment::CompanyDataJob.perform_later(company_id: 123)
  class CompanyDataJob < ApplicationJob
    queue_as :enrichment
    sidekiq_options retry: 5

    retry_on Faraday::TooManyRequestsError, wait: :polynomially_longer, attempts: 5
    retry_on Faraday::ConnectionFailed, wait: 10.seconds, attempts: 3
    discard_on ActiveRecord::RecordNotFound

    # @param company_id [Integer] the company to enrich
    # @param force [Boolean] force re-enrichment even if recently done
    def perform(company_id:, force: false)
      company = Company.find(company_id)
      return if !force && company.enriched_recently?

      Enrichment::CompanyDataService.new(company:, force:).call
    rescue Faraday::Error => e
      Rails.logger.error(
        "Enrichment failed for company #{company_id}: #{e.class} - #{e.message}"
      )
      raise # Re-raise to trigger Sidekiq retry
    end
  end
end
```

---

## Job Spec Example

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Sync::AirtableImportJob, type: :job do
  subject(:job) { described_class }

  describe '#perform' do
    let(:import) { create(:import, :pending) }

    it 'delegates to the import service' do
      service = instance_double(Sync::AirtableImportService, call: success_result)
      allow(Sync::AirtableImportService).to receive(:new)
        .with(import:)
        .and_return(service)

      job.perform_now(import.id)

      expect(service).to have_received(:call)
    end

    it 'marks the import as started' do
      allow(Sync::AirtableImportService).to receive(:new).and_return(
        instance_double(Sync::AirtableImportService, call: success_result)
      )

      job.perform_now(import.id)

      expect(import.reload).to be_completed
    end

    context 'when the import is already completed' do
      let(:import) { create(:import, :completed) }

      it 'skips processing' do
        expect(Sync::AirtableImportService).not_to receive(:new)

        job.perform_now(import.id)
      end
    end

    context 'when the record does not exist' do
      it 'logs and does not raise' do
        expect(Rails.logger).to receive(:warn).with(/not found/)

        expect { job.perform_now(99999) }.not_to raise_error
      end
    end
  end

  describe 'queue configuration' do
    it 'uses the default queue' do
      expect(described_class.new.queue_name).to eq('default')
    end
  end

  def success_result
    OpenStruct.new(success?: true, imported_count: 10, error_count: 0, errors: [])
  end
end
```

---

## Queue Configuration Reference

| Queue          | Purpose                            | Priority |
|----------------|------------------------------------|----------|
| `default`      | Standard processing jobs           | Normal   |
| `notifications`| Email, push, in-app notifications  | High     |
| `enrichment`   | External API data enrichment       | Low      |
| `low_priority`  | Maintenance, cleanup, reporting    | Lowest   |
| `critical`     | Payment processing, auth           | Highest  |
