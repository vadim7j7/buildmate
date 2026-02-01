# Service Object Examples

Real-world service object examples based on production Rails patterns.

---

## Example 1: Namespaced Import Service

A service that handles bulk importing of profiles from a CSV file.

```ruby
# frozen_string_literal: true

module BulkImport
  # Imports profiles from a CSV file, creating or updating records
  # and collecting errors for invalid rows.
  #
  # @example
  #   result = BulkImport::ProfilesService.new(file:, user:).call
  #   result.imported_count  # => 42
  #   result.errors          # => ["Row 3: Email is invalid"]
  class ProfilesService < ApplicationService
    # @param file [ActionDispatch::Http::UploadedFile] the CSV file to import
    # @param user [User] the user performing the import
    # @param dry_run [Boolean] if true, validate without persisting
    def initialize(file:, user:, dry_run: false)
      @file = file
      @user = user
      @dry_run = dry_run
      @imported_count = 0
      @errors = []
    end

    # Processes the CSV file and imports valid profiles.
    #
    # @return [OpenStruct] result with imported_count, errors, and success?
    def call
      return failure_result('File is required') if file.blank?
      return failure_result('File is empty') if csv_rows.empty?

      ActiveRecord::Base.transaction do
        csv_rows.each_with_index do |row, index|
          import_row(row, index + 2) # +2 for header and 1-indexing
        end

        raise ActiveRecord::Rollback if dry_run
      end

      success_result
    end

    private

    attr_reader :file, :user, :dry_run, :imported_count, :errors

    def csv_rows
      @csv_rows ||= CSV.parse(file.read, headers: true)
    end

    def import_row(row, row_number)
      profile = Profile.find_or_initialize_by(email: row['email']&.strip&.downcase)
      profile.assign_attributes(
        name: row['name'],
        bio: row['bio'],
        imported_by: user
      )

      if profile.save
        @imported_count += 1
      else
        @errors << "Row #{row_number}: #{profile.errors.full_messages.join(', ')}"
      end
    end

    def success_result
      OpenStruct.new(
        success?: errors.empty?,
        imported_count:,
        errors:
      )
    end

    def failure_result(message)
      OpenStruct.new(
        success?: false,
        imported_count: 0,
        errors: [message]
      )
    end
  end
end
```

---

## Example 2: Singleton Utility Service

A service that provides string manipulation utilities for the application.

```ruby
# frozen_string_literal: true

# Provides string transformation utilities used across the application
# for normalizing user input and generating slugs.
#
# @example
#   StringServices.normalize_name('  JANE  DOE  ')  # => 'Jane Doe'
#   StringServices.generate_slug('My Company Name')  # => 'my-company-name'
module StringServices
  module_function

  # Normalizes a name by stripping whitespace and title-casing.
  #
  # @param name [String] the raw name input
  # @return [String] the normalized name
  def normalize_name(name)
    return '' if name.blank?

    name.strip.squeeze(' ').split.map(&:capitalize).join(' ')
  end

  # Generates a URL-safe slug from a string.
  #
  # @param text [String] the text to slugify
  # @return [String] the URL-safe slug
  def generate_slug(text)
    return '' if text.blank?

    text.strip
        .downcase
        .gsub(/[^a-z0-9\s-]/, '')
        .gsub(/[\s-]+/, '-')
        .gsub(/\A-|-\z/, '')
  end

  # Truncates text to a maximum length with ellipsis.
  #
  # @param text [String] the text to truncate
  # @param max_length [Integer] maximum character count
  # @return [String] truncated text
  def truncate_with_ellipsis(text, max_length: 200)
    return '' if text.blank?
    return text if text.length <= max_length

    "#{text[0...(max_length - 3)]}..."
  end
end
```

---

## Example 3: External API Integration Service

A service that syncs company data from an external provider.

```ruby
# frozen_string_literal: true

module Sync
  # Fetches and updates company data from Clearbit's enrichment API.
  # Handles rate limiting, retries, and partial data gracefully.
  #
  # @example
  #   Sync::CompanyEnrichmentService.new(company:).call
  class CompanyEnrichmentService < ApplicationService
    ENRICHMENT_FIELDS = %w[name domain industry size founded_year description].freeze

    # @param company [Company] the company to enrich
    # @param force [Boolean] force re-enrichment even if recently synced
    def initialize(company:, force: false)
      @company = company
      @force = force
    end

    # Enriches the company with data from Clearbit.
    #
    # @return [Boolean] true if enrichment was successful
    def call
      return false unless should_enrich?

      data = fetch_enrichment_data
      return false if data.blank?

      update_company(data)
      record_sync_timestamp
      true
    rescue Faraday::Error => e
      handle_api_error(e)
      false
    end

    private

    attr_reader :company, :force

    def should_enrich?
      return true if force

      company.last_enriched_at.blank? || company.last_enriched_at < 7.days.ago
    end

    def fetch_enrichment_data
      response = clearbit_client.get("/v2/companies/find?domain=#{company.domain}")
      return nil unless response.status == 200

      JSON.parse(response.body)
    end

    def update_company(data)
      attributes = ENRICHMENT_FIELDS.each_with_object({}) do |field, hash|
        hash[field] = data[field] if data[field].present?
      end

      company.update!(attributes) if attributes.any?
    end

    def record_sync_timestamp
      company.update_column(:last_enriched_at, Time.current)
    end

    def handle_api_error(error)
      Rails.logger.error(
        "Clearbit enrichment failed for company #{company.id}: #{error.message}"
      )

      if error.respond_to?(:response) && error.response&.dig(:status) == 429
        Sync::CompanyEnrichmentJob.set(wait: 1.hour).perform_later(company.id)
      end
    end

    def clearbit_client
      @clearbit_client ||= Faraday.new(url: 'https://company.clearbit.com') do |conn|
        conn.request :authorization, 'Bearer', ENV.fetch('CLEARBIT_API_KEY')
        conn.request :retry, max: 2, interval: 0.5
        conn.response :raise_error
      end
    end
  end
end
```

---

## Spec Example for Service

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BulkImport::ProfilesService do
  subject(:service) { described_class.new(file:, user:) }

  let(:user) { create(:user, :admin) }
  let(:file) { fixture_file_upload('spec/fixtures/profiles.csv', 'text/csv') }

  describe '#call' do
    context 'when the file is valid' do
      it 'imports profiles from CSV rows' do
        result = service.call

        expect(result.success?).to be(true)
        expect(result.imported_count).to eq(3)
        expect(result.errors).to be_empty
      end
    end

    context 'when some rows are invalid' do
      let(:file) { fixture_file_upload('spec/fixtures/profiles_with_errors.csv', 'text/csv') }

      it 'imports valid rows and collects errors' do
        result = service.call

        expect(result.imported_count).to eq(2)
        expect(result.errors).to include(match(/Row 4/))
      end
    end

    context 'when the file is blank' do
      let(:file) { nil }

      it 'returns a failure result' do
        result = service.call

        expect(result.success?).to be(false)
        expect(result.errors).to include('File is required')
      end
    end

    context 'when dry_run is true' do
      subject(:service) { described_class.new(file:, user:, dry_run: true) }

      it 'validates without persisting' do
        expect { service.call }.not_to change(Profile, :count)
      end
    end
  end
end
```
