# Ruby Style Guide

Style conventions for all Ruby code in this Rails application. These rules are
enforced by rubocop and must be followed by all agents.

---

## 1. File Headers

Every Ruby file MUST begin with the frozen string literal pragma:

```ruby
# frozen_string_literal: true
```

No exceptions. This is the very first line before any blank lines or comments.

---

## 2. String Literals

**Single quotes** for all strings. Double quotes only when interpolation is needed.

```ruby
# GOOD
name = 'Jane Doe'
status = 'active'
query = "Hello, #{user.name}!"

# BAD
name = "Jane Doe"
status = "active"
```

---

## 3. Hash Shorthand

Use Ruby 3.1+ hash shorthand when the key and value have the same name:

```ruby
# GOOD
{ id:, name:, email:, created_at: }

# BAD
{ id: id, name: name, email: email, created_at: created_at }
```

This applies to method calls, render statements, and service constructors:

```ruby
# GOOD
UserService.new(user:, provider:)
render json: { profile:, meta: }

# BAD
UserService.new(user: user, provider: provider)
```

---

## 4. Guard Clauses

Use guard clauses (early returns) instead of nested conditionals:

```ruby
# GOOD
def call
  return if user.blank?
  return unless user.active?

  perform_action
end

# BAD
def call
  if user.present?
    if user.active?
      perform_action
    end
  end
end
```

---

## 5. YARD Documentation

All public methods MUST have YARD documentation:

```ruby
# Syncs the user profile with the external provider.
#
# @param user [User] the user to sync
# @param provider [String] the provider name (e.g., 'linkedin')
# @return [Boolean] true if sync was successful
# @raise [ExternalApi::Error] if the API call fails
#
# @example
#   sync_profile(user, 'linkedin')
def sync_profile(user, provider)
  # ...
end
```

### Required Tags

- `@param` for every parameter
- `@return` for the return value
- `@raise` for exceptions that may be raised
- `@example` for non-obvious usage

### Class-Level Documentation

```ruby
# Represents a candidate profile with professional information
# and company associations.
#
# @!attribute name [rw]
#   @return [String] the candidate's display name
class Profile < ApplicationRecord
```

---

## 6. Naming Conventions

| Entity        | Convention        | Example                          |
|---------------|-------------------|----------------------------------|
| Class         | CamelCase         | `ProfilePresenter`               |
| Module        | CamelCase         | `BulkImport`                     |
| Method        | snake_case        | `sync_profile`                   |
| Variable      | snake_case        | `current_user`                   |
| Constant      | SCREAMING_SNAKE   | `MAX_RETRY_COUNT`                |
| Predicate     | ends with `?`     | `active?`, `completed?`          |
| Bang method   | ends with `!`     | `save!`, `destroy!`              |
| File name     | snake_case        | `profile_presenter.rb`           |
| Factory       | snake_case symbol | `:profile`, `:user`              |

### Service Naming

- Module: business domain (`Users`, `BulkImport`, `Sync`)
- Class: action + noun + `Service` (`SyncProfileService`, `ProfilesService`)

### Presenter Naming

- Model name + `Presenter` (`ProfilePresenter`, `CompanyPresenter`)

### Job Naming

- Module: business domain (`Sync`, `Notifications`, `Maintenance`)
- Class: action + noun + `Job` (`AirtableImportJob`, `WelcomeJob`)

---

## 7. Method Organization

Within a class, organize methods in this order:

1. `include` / `extend` statements
2. Constants
3. Class methods (`self.method`)
4. Public instance methods
5. `private` keyword
6. Private instance methods (ordered by usage)

```ruby
class ProfileService < ApplicationService
  include Loggable

  MAX_RETRIES = 3

  def self.supported_providers
    %w[linkedin github]
  end

  def call
    fetch_data
    transform_data
    persist_data
  end

  private

  def fetch_data
    # ...
  end

  def transform_data
    # ...
  end

  def persist_data
    # ...
  end
end
```

---

## 8. Scope Conventions

```ruby
# Simple boolean scope
scope :active, -> { where(active: true) }

# Scope with parameter (use lambda arg)
scope :by_status, ->(status) { where(status:) }

# Scope that returns all when param is blank (composable)
scope :search, ->(query) {
  return all if query.blank?

  where('name ILIKE ?', "%#{query}%")
}

# Scope ordering
scope :recent, -> { order(created_at: :desc) }
scope :alphabetical, -> { order(:name) }

# Scope with eager loading
scope :with_associations, -> { includes(:company, :skills) }
```

---

## 9. Association Conventions

```ruby
# Order: belongs_to, has_many, has_one
belongs_to :user
belongs_to :company, optional: true

has_many :experiences, dependent: :destroy
has_many :skills, through: :profile_skills

has_one :resume, dependent: :destroy
```

---

## 10. N+1 Query Prevention

**ALWAYS** use `includes()` when accessing associations in loops or serialization:

```ruby
# GOOD
profiles = Profile.includes(:company, :skills).where(active: true)
profiles.each { |p| p.company.name }  # No N+1

# BAD
profiles = Profile.where(active: true)
profiles.each { |p| p.company.name }  # N+1 query per profile!
```

Use `preload()` when you need separate queries (e.g., complex WHERE on association).
Use `eager_load()` when you need to filter by associated table columns.

---

## 11. Error Handling

```ruby
# GOOD - Rescue specific exceptions
rescue ActiveRecord::RecordNotFound => e
  Rails.logger.warn("Record not found: #{e.message}")

# GOOD - Rescue multiple specific exceptions
rescue Faraday::TimeoutError, Faraday::ConnectionFailed => e
  Rails.logger.error("API error: #{e.class} - #{e.message}")

# BAD - Bare rescue
rescue => e
  # catches everything including syntax errors

# BAD - Rescue StandardError without context
rescue StandardError
  nil
```

---

## 12. Conditional Formatting

```ruby
# Single-line conditionals for simple cases
return if user.blank?
send_email if user.notifications_enabled?

# Multi-line for complex conditions
if user.active? && user.profile.complete?
  notify_user
  update_status
end

# Unless for negative single conditions
render_error unless user.authorized?

# NEVER use unless with else
# BAD
unless user.active?
  deactivate
else
  activate
end

# GOOD
if user.active?
  activate
else
  deactivate
end
```

---

## 13. Collection Methods

```ruby
# Prefer &: for simple transformations
names = users.map(&:name)
active = users.select(&:active?)

# Use blocks for complex logic
names = users.map { |u| "#{u.first_name} #{u.last_name}" }

# Prefer each_with_object over inject/reduce for building hashes
result = items.each_with_object({}) do |item, hash|
  hash[item.id] = item.name
end

# Use find_each for large datasets
Profile.active.find_each(batch_size: 500) do |profile|
  process(profile)
end
```

---

## 14. Rubocop Enforcement

These rules are enforced by rubocop. Run before every commit:

```bash
# Check for violations
bundle exec rubocop

# Auto-fix safe violations
bundle exec rubocop -A

# Check specific files
bundle exec rubocop app/services/users/sync_service.rb
```

Key rubocop rules:
- `Style/StringLiterals: single_quotes`
- `Style/FrozenStringLiteralComment: always`
- `Style/HashSyntax: ruby19` (with shorthand)
- `Style/GuardClause: true`
- `Layout/LineLength: Max 120`
- `Metrics/MethodLength: Max 20`
- `Metrics/ClassLength: Max 150`
