# FactoryBot Factory Patterns

Reference patterns for FactoryBot factories. All factories live in `spec/factories/`
and follow these conventions.

---

## Basic Factory with Sequences and Faker

```ruby
# spec/factories/profiles.rb
# frozen_string_literal: true

FactoryBot.define do
  factory :profile do
    user
    company

    name { Faker::Name.name }
    sequence(:email) { |n| "user#{n}@example.com" }
    bio { Faker::Lorem.paragraph(sentence_count: 3) }
    active { true }
    role { :member }
    created_at { Time.current }

    # -- Traits --
    trait :inactive do
      active { false }
    end

    trait :admin do
      role { :admin }
    end

    trait :with_experiences do
      after(:create) do |profile|
        create_list(:experience, 3, profile:)
      end
    end

    trait :with_skills do
      after(:create) do |profile|
        skills = create_list(:skill, 5)
        skills.each { |skill| create(:profile_skill, profile:, skill:) }
      end
    end

    trait :with_resume do
      after(:create) do |profile|
        create(:resume, profile:)
      end
    end

    trait :complete do
      with_experiences
      with_skills
      with_resume
    end
  end
end
```

---

## Factory with Associations

```ruby
# spec/factories/experiences.rb
# frozen_string_literal: true

FactoryBot.define do
  factory :experience do
    profile
    company

    title { Faker::Job.title }
    description { Faker::Lorem.paragraph }
    start_date { Faker::Date.between(from: 5.years.ago, to: 1.year.ago) }
    end_date { nil }
    current { true }

    trait :past do
      current { false }
      end_date { Faker::Date.between(from: 1.year.ago, to: 1.month.ago) }
    end

    trait :at_company do
      transient do
        company_name { 'Acme Corp' }
      end

      company { association :company, name: company_name }
    end
  end
end
```

---

## Factory with Enum and State Variants

```ruby
# spec/factories/imports.rb
# frozen_string_literal: true

FactoryBot.define do
  factory :import do
    user
    sequence(:file_name) { |n| "import_#{n}.csv" }
    status { :pending }
    row_count { 0 }
    imported_count { 0 }
    error_count { 0 }

    trait :pending do
      status { :pending }
    end

    trait :processing do
      status { :processing }
      started_at { Time.current }
    end

    trait :completed do
      status { :completed }
      started_at { 1.hour.ago }
      completed_at { Time.current }
      row_count { 100 }
      imported_count { 100 }
    end

    trait :failed do
      status { :failed }
      started_at { 1.hour.ago }
      completed_at { Time.current }
      error_count { 5 }
      error_messages { ['Row 1: invalid email', 'Row 3: missing name'] }
    end
  end
end
```

---

## Factory with Transient Attributes

```ruby
# spec/factories/users.rb
# frozen_string_literal: true

FactoryBot.define do
  factory :user do
    sequence(:email) { |n| "user#{n}@example.com" }
    password { 'password123' }
    password_confirmation { 'password123' }
    confirmed_at { Time.current }

    transient do
      profile_count { 0 }
    end

    after(:create) do |user, evaluator|
      create_list(:profile, evaluator.profile_count, user:) if evaluator.profile_count.positive?
    end

    trait :admin do
      role { :admin }
    end

    trait :unconfirmed do
      confirmed_at { nil }
    end

    trait :with_profile do
      after(:create) do |user|
        create(:profile, user:)
      end
    end

    trait :with_multiple_profiles do
      transient do
        profile_count { 3 }
      end
    end
  end
end
```

---

## Factory with JSONB and Complex Types

```ruby
# spec/factories/companies.rb
# frozen_string_literal: true

FactoryBot.define do
  factory :company do
    sequence(:name) { |n| "Company #{n}" }
    domain { Faker::Internet.domain_name }
    size { %w[startup small medium large enterprise].sample }
    industry { Faker::Company.industry }

    # JSONB fields
    metadata do
      {
        founded_year: rand(1990..2024),
        headquarters: Faker::Address.city,
        technologies: Faker::Lorem.words(number: 5)
      }
    end

    settings do
      {
        notifications_enabled: true,
        sync_frequency: 'daily',
        allowed_domains: [domain]
      }
    end

    trait :with_profiles do
      after(:create) do |company|
        create_list(:profile, 5, company:)
      end
    end

    trait :enterprise do
      size { 'enterprise' }
      settings do
        {
          notifications_enabled: true,
          sync_frequency: 'hourly',
          sso_enabled: true,
          allowed_domains: [domain]
        }
      end
    end
  end
end
```

---

## Factory Usage Examples

```ruby
# Basic creation
profile = create(:profile)
profile = build(:profile)  # Does not persist

# With traits
admin = create(:profile, :admin)
inactive = create(:profile, :inactive)
complete = create(:profile, :complete)

# With attribute overrides
profile = create(:profile, name: 'Custom Name', email: 'custom@example.com')

# With traits AND overrides
profile = create(:profile, :admin, name: 'Admin User')

# Lists
profiles = create_list(:profile, 5)
profiles = create_list(:profile, 3, :with_experiences)

# With transient attributes
user = create(:user, profile_count: 3)

# Associations
experience = create(:experience, :at_company, company_name: 'Google')

# Build (no persistence) for unit tests
profile = build_stubbed(:profile)  # Assigns an ID but does not persist
```

---

## Factory Organization Rules

1. One factory per file, named after the model (plural): `spec/factories/profiles.rb`
2. Use `sequence` for unique attributes (emails, slugs, etc.)
3. Use `Faker` for realistic data
4. Use `trait` for common variations
5. Use `transient` for configuration that does not map to columns
6. Use `after(:create)` for associated records that need persistence
7. Keep factories minimal; traits add optional complexity
8. Do not define default values that violate validations
