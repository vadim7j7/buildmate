# Model Examples

Production-ready ActiveRecord model examples demonstrating associations, validations,
scopes, callbacks, enums, and proper ordering conventions.

---

## Example 1: Primary Model with Full Features

```ruby
# frozen_string_literal: true

# Represents a candidate profile with professional information.
#
# @!attribute name [rw]
#   @return [String] the candidate's display name
# @!attribute email [rw]
#   @return [String] the candidate's email address
# @!attribute status [rw]
#   @return [String] current profile status (active, inactive, archived)
class Profile < ApplicationRecord
  # -- Associations --
  belongs_to :user
  belongs_to :company, optional: true
  has_many :experiences, dependent: :destroy
  has_many :profile_skills, dependent: :destroy
  has_many :skills, through: :profile_skills
  has_many :interviews, dependent: :destroy
  has_one :resume, dependent: :destroy
  has_paper_trail

  # -- Validations --
  validates :name, presence: true, length: { maximum: 255 }
  validates :email, presence: true,
                    uniqueness: { case_sensitive: false },
                    format: { with: URI::MailTo::EMAIL_REGEXP }
  validates :bio, length: { maximum: 5000 }
  validates :phone, format: { with: /\A\+?[\d\s\-()]+\z/, allow_blank: true }

  # -- Enums --
  enum :status, { active: 0, inactive: 1, archived: 2 }, default: :active
  enum :visibility, { private_profile: 0, public_profile: 1 }, default: :private_profile

  # -- Scopes --
  scope :active, -> { where(status: :active) }
  scope :recent, -> { order(created_at: :desc) }
  scope :with_company, -> { where.not(company_id: nil) }
  scope :search, ->(query) {
    return all if query.blank?

    where('name ILIKE ? OR email ILIKE ?', "%#{query}%", "%#{query}%")
  }
  scope :by_company, ->(company_id) { where(company_id:) if company_id.present? }
  scope :with_associations, -> { includes(:company, :skills, :experiences) }

  # -- Callbacks --
  before_validation :normalize_email
  before_validation :set_default_status, on: :create
  after_create_commit :send_welcome_notification
  after_update_commit :sync_to_search_index, if: :searchable_fields_changed?

  # -- Public Methods --

  # Returns the full display name with company context.
  #
  # @return [String] formatted display name
  def display_name
    company ? "#{name} (#{company.name})" : name
  end

  # Checks if the profile has been recently updated.
  #
  # @return [Boolean] true if updated within the last 30 days
  def recently_updated?
    updated_at > 30.days.ago
  end

  private

  def normalize_email
    self.email = email&.strip&.downcase
  end

  def set_default_status
    self.status ||= :active
  end

  def send_welcome_notification
    Notifications::WelcomeJob.perform_later(user_id: user.id, profile_id: id)
  end

  def sync_to_search_index
    Search::IndexProfileJob.perform_later(id)
  end

  def searchable_fields_changed?
    saved_change_to_name? || saved_change_to_bio? || saved_change_to_status?
  end
end
```

### Migration for Profile

```ruby
# frozen_string_literal: true

class CreateProfiles < ActiveRecord::Migration[7.1]
  def change
    create_table :profiles do |t|
      t.references :user, null: false, foreign_key: true, index: true
      t.references :company, foreign_key: true, index: true
      t.string :name, null: false
      t.string :email, null: false
      t.text :bio
      t.string :phone
      t.integer :status, default: 0, null: false
      t.integer :visibility, default: 0, null: false
      t.boolean :active, default: true, null: false
      t.timestamps
    end

    add_index :profiles, :email, unique: true
    add_index :profiles, :status
    add_index :profiles, :active
    add_index :profiles, [:user_id, :email], unique: true
  end
end
```

---

## Example 2: Join Model

```ruby
# frozen_string_literal: true

# Join table connecting profiles to skills with proficiency level.
#
# @!attribute proficiency [rw]
#   @return [String] skill proficiency level
class ProfileSkill < ApplicationRecord
  # -- Associations --
  belongs_to :profile
  belongs_to :skill

  # -- Validations --
  validates :profile_id, uniqueness: { scope: :skill_id, message: 'already has this skill' }

  # -- Enums --
  enum :proficiency, { beginner: 0, intermediate: 1, advanced: 2, expert: 3 }, default: :intermediate

  # -- Scopes --
  scope :by_proficiency, ->(level) { where(proficiency: level) }
  scope :recent, -> { order(created_at: :desc) }
end
```

### Migration for Join Model

```ruby
# frozen_string_literal: true

class CreateProfileSkills < ActiveRecord::Migration[7.1]
  def change
    create_table :profile_skills do |t|
      t.references :profile, null: false, foreign_key: true
      t.references :skill, null: false, foreign_key: true
      t.integer :proficiency, default: 1, null: false
      t.timestamps
    end

    add_index :profile_skills, [:profile_id, :skill_id], unique: true
  end
end
```

---

## Example 3: Model with JSONB and Polymorphic Association

```ruby
# frozen_string_literal: true

# Represents an activity log entry for audit trail purposes.
#
# @!attribute action [rw]
#   @return [String] the action performed (created, updated, deleted)
# @!attribute metadata [rw]
#   @return [Hash] additional context about the activity
class Activity < ApplicationRecord
  # -- Associations --
  belongs_to :user
  belongs_to :trackable, polymorphic: true

  # -- Validations --
  validates :action, presence: true, inclusion: { in: %w[created updated deleted] }
  validates :metadata, presence: true

  # -- Scopes --
  scope :recent, -> { order(created_at: :desc) }
  scope :by_action, ->(action) { where(action:) }
  scope :for_user, ->(user) { where(user:) }
  scope :for_trackable, ->(trackable_type, trackable_id) {
    where(trackable_type:, trackable_id:)
  }
  scope :this_week, -> { where(created_at: 1.week.ago..) }

  # -- Public Methods --

  # Returns a human-readable description of the activity.
  #
  # @return [String] formatted activity description
  def description
    "#{user.name} #{action} #{trackable_type.underscore.humanize.downcase} ##{trackable_id}"
  end
end
```

### Migration with JSONB

```ruby
# frozen_string_literal: true

class CreateActivities < ActiveRecord::Migration[7.1]
  def change
    create_table :activities do |t|
      t.references :user, null: false, foreign_key: true
      t.references :trackable, polymorphic: true, null: false
      t.string :action, null: false
      t.jsonb :metadata, default: {}, null: false
      t.timestamps
    end

    add_index :activities, :action
    add_index :activities, :created_at
    add_index :activities, :metadata, using: :gin
  end
end
```

---

## Example 4: Model with Enum and State Machine Logic

```ruby
# frozen_string_literal: true

# Represents a data import job with status tracking.
#
# @!attribute status [rw]
#   @return [String] current import status
# @!attribute file_name [rw]
#   @return [String] name of the imported file
class Import < ApplicationRecord
  # -- Associations --
  belongs_to :user
  has_many :import_rows, dependent: :destroy

  # -- Validations --
  validates :file_name, presence: true
  validates :status, presence: true

  # -- Enums --
  enum :status, {
    pending: 0,
    processing: 1,
    completed: 2,
    failed: 3,
    cancelled: 4
  }, default: :pending

  # -- Scopes --
  scope :active, -> { where(status: %i[pending processing]) }
  scope :finished, -> { where(status: %i[completed failed cancelled]) }
  scope :recent, -> { order(created_at: :desc) }

  # -- Public Methods --

  # Transitions the import to processing state.
  #
  # @return [Boolean] true if transition was successful
  def start!
    return false unless pending?

    update!(status: :processing, started_at: Time.current)
  end

  # Marks the import as completed with counts.
  #
  # @param imported_count [Integer] number of successfully imported rows
  # @param error_count [Integer] number of failed rows
  # @return [Boolean] true if transition was successful
  def complete!(imported_count:, error_count: 0)
    return false unless processing?

    update!(
      status: :completed,
      completed_at: Time.current,
      imported_count:,
      error_count:
    )
  end

  # Checks if the import finished recently enough to skip re-import.
  #
  # @return [Boolean] true if completed within the last hour
  def completed_recently?
    completed? && completed_at > 1.hour.ago
  end
end
```

---

## Model Ordering Convention

Always organize model internals in this order:

1. `include` / `extend` modules
2. Constants
3. Associations (`belongs_to`, `has_many`, `has_one`)
4. Validations
5. Enums
6. Scopes
7. Callbacks
8. Public instance methods
9. Private methods
