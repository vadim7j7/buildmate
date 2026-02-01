# Presenter Examples

Production-ready presenter examples demonstrating BasePresenter inheritance, the call
method pattern, nested data, conditional fields, and collection handling.

---

## BasePresenter

```ruby
# frozen_string_literal: true

# Base class for all presenters. Accepts a record or collection and
# provides a consistent interface via the #call method.
#
# @example
#   ProfilePresenter.new(profile).call     # single record
#   ProfilePresenter.new(profiles).call    # collection
class BasePresenter
  attr_reader :record

  # @param record [ApplicationRecord, ActiveRecord::Relation, Array] the data to present
  def initialize(record)
    @record = record
  end

  # @return [Hash, Array<Hash>] serialized data
  def call
    raise NotImplementedError, "#{self.class}#call must be implemented"
  end
end
```

---

## Example 1: Standard Presenter with Nested Data

```ruby
# frozen_string_literal: true

# Presents profile data for API responses, including nested company
# and skills data.
#
# @example
#   ProfilePresenter.new(profile).call
#   # => { id: 1, name: "Jane", email: "jane@example.com", ... }
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
      status: profile.status,
      active: profile.active,
      company: company_data(profile),
      skills: skills_data(profile),
      experience_count: profile.experiences.size,
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

  def skills_data(profile)
    profile.skills.map do |skill|
      {
        id: skill.id,
        name: skill.name
      }
    end
  end
end
```

---

## Example 2: Presenter with Conditional Fields

```ruby
# frozen_string_literal: true

# Presents company data with optional detail level.
#
# @example
#   CompanyPresenter.new(company).call
#   CompanyPresenter.new(company, detailed: true).call
class CompanyPresenter < BasePresenter
  # @param record [Company, Array<Company>] the company record(s)
  # @param detailed [Boolean] include extended information
  def initialize(record, detailed: false)
    super(record)
    @detailed = detailed
  end

  # @return [Hash, Array<Hash>] serialized company data
  def call
    if record.respond_to?(:each)
      record.map { |r| present_one(r) }
    else
      present_one(record)
    end
  end

  private

  def present_one(company)
    data = {
      id: company.id,
      name: company.name,
      domain: company.domain,
      industry: company.industry,
      size: company.size,
      profile_count: company.profiles.size
    }

    data.merge!(detailed_data(company)) if @detailed
    data
  end

  def detailed_data(company)
    {
      description: company.description,
      founded_year: company.metadata&.dig('founded_year'),
      headquarters: company.metadata&.dig('headquarters'),
      technologies: company.metadata&.dig('technologies') || [],
      settings: sanitized_settings(company),
      created_at: company.created_at.iso8601,
      updated_at: company.updated_at.iso8601
    }
  end

  def sanitized_settings(company)
    return {} unless company.settings

    company.settings.slice('notifications_enabled', 'sync_frequency')
  end
end
```

---

## Example 3: Presenter with Nested Collection

```ruby
# frozen_string_literal: true

# Presents candidate data with full experience history.
#
# @example
#   CandidatePresenter.new(candidate).call
class CandidatePresenter < BasePresenter
  # @return [Hash, Array<Hash>] serialized candidate data
  def call
    if record.respond_to?(:each)
      record.map { |r| present_one(r) }
    else
      present_one(record)
    end
  end

  private

  def present_one(candidate)
    {
      id: candidate.id,
      name: candidate.name,
      email: candidate.email,
      headline: candidate.bio&.truncate(120),
      current_company: current_company_name(candidate),
      experiences: experiences_data(candidate),
      skills: candidate.skills.pluck(:name),
      applied_at: candidate.created_at.iso8601
    }
  end

  def current_company_name(candidate)
    candidate.experiences.find_by(current: true)&.company&.name
  end

  def experiences_data(candidate)
    candidate.experiences.order(start_date: :desc).map do |exp|
      {
        id: exp.id,
        title: exp.title,
        company_name: exp.company&.name,
        start_date: exp.start_date.iso8601,
        end_date: exp.end_date&.iso8601,
        current: exp.current
      }
    end
  end
end
```

---

## Presenter Spec Example

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe ProfilePresenter do
  describe '#call' do
    context 'with a single record' do
      let(:profile) { create(:profile, :with_experiences, company: create(:company)) }

      it 'returns a hash with profile data' do
        result = described_class.new(profile).call

        expect(result).to include(
          id: profile.id,
          name: profile.name,
          email: profile.email,
          status: profile.status,
          active: profile.active
        )
      end

      it 'includes company data' do
        result = described_class.new(profile).call

        expect(result[:company]).to include(
          id: profile.company.id,
          name: profile.company.name
        )
      end

      it 'formats timestamps as ISO 8601' do
        result = described_class.new(profile).call

        expect(result[:created_at]).to match(/\d{4}-\d{2}-\d{2}T/)
      end
    end

    context 'with a collection' do
      let(:profiles) { create_list(:profile, 3) }

      it 'returns an array of hashes' do
        result = described_class.new(profiles).call

        expect(result).to be_an(Array)
        expect(result.size).to eq(3)
        expect(result.first).to have_key(:id)
      end
    end

    context 'when company is nil' do
      let(:profile) { create(:profile, company: nil) }

      it 'returns nil for company data' do
        result = described_class.new(profile).call

        expect(result[:company]).to be_nil
      end
    end
  end
end
```
