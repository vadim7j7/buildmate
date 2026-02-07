# Rails Common Pitfalls & Anti-Patterns

Common mistakes and performance issues in Ruby on Rails applications. All agents
must recognize and avoid these patterns.

---

## 1. N+1 Query Problem

The most common Rails performance issue. Occurs when loading associations in a loop.

```ruby
# WRONG - N+1 queries (1 query for posts + N queries for users)
posts = Post.all
posts.each do |post|
  puts post.user.name  # Each iteration queries the database
end

# CORRECT - eager loading with includes
posts = Post.includes(:user).all
posts.each do |post|
  puts post.user.name  # No additional queries
end

# CORRECT - preload for read-only associations
posts = Post.preload(:user, :comments).all

# CORRECT - eager_load for filtering on associations
posts = Post.eager_load(:user).where(users: { active: true })

# CORRECT - strict_loading to catch N+1 in development
class Post < ApplicationRecord
  self.strict_loading_by_default = true  # Rails 7+
end

# Or per-query
Post.strict_loading.all
```

### Nested N+1

```ruby
# WRONG - nested N+1
posts = Post.includes(:comments)
posts.each do |post|
  post.comments.each do |comment|
    puts comment.user.name  # N+1 on comment.user!
  end
end

# CORRECT - nested includes
posts = Post.includes(comments: :user)
```

### Bullet Gem for Detection

```ruby
# Gemfile (development only)
group :development do
  gem 'bullet'
end

# config/environments/development.rb
config.after_initialize do
  Bullet.enable = true
  Bullet.alert = true
  Bullet.rails_logger = true
  Bullet.add_footer = true
end
```

---

## 2. Counter Cache Missing

Don't count associations in loops. Use counter caches.

```ruby
# WRONG - COUNT query for each post
posts.each do |post|
  puts "#{post.title}: #{post.comments.count} comments"
end

# CORRECT - counter cache column
class Comment < ApplicationRecord
  belongs_to :post, counter_cache: true
end

# Migration
add_column :posts, :comments_count, :integer, default: 0, null: false

# Reset existing counts
Post.find_each do |post|
  Post.reset_counters(post.id, :comments)
end

# Now this uses the cached count
posts.each do |post|
  puts "#{post.title}: #{post.comments_count} comments"
end
```

---

## 3. Loading All Records

Never load unbounded datasets into memory.

```ruby
# WRONG - loads all records into memory
User.all.each do |user|
  user.send_newsletter
end

# CORRECT - batch processing with find_each
User.subscribed.find_each(batch_size: 1000) do |user|
  user.send_newsletter
end

# CORRECT - find_in_batches for batch operations
User.subscribed.find_in_batches(batch_size: 1000) do |batch|
  NewsletterMailer.bulk_send(batch.pluck(:email))
end

# CORRECT - in_batches for ActiveRecord operations
User.inactive.in_batches(of: 1000) do |batch|
  batch.update_all(archived: true)
end
```

---

## 4. Unindexed Queries

Always add indexes for columns used in WHERE, JOIN, and ORDER clauses.

```ruby
# Check for missing indexes in development
# Add to Gemfile
gem 'lol_dba'  # Run: lol_dba db:find_indexes

# Common missing indexes
class AddMissingIndexes < ActiveRecord::Migration[7.0]
  def change
    # Foreign keys (ALWAYS index these)
    add_index :comments, :post_id
    add_index :comments, :user_id

    # Columns used in WHERE clauses
    add_index :users, :email, unique: true
    add_index :users, :active
    add_index :orders, :status

    # Columns used in ORDER BY
    add_index :posts, :created_at
    add_index :posts, :published_at

    # Compound indexes for common query patterns
    add_index :orders, [:user_id, :created_at]
    add_index :posts, [:published, :created_at]

    # Partial indexes for common filtered queries
    add_index :users, :email, where: "deleted_at IS NULL", name: "index_active_users_on_email"
  end
end
```

### Explain Queries

```ruby
# In rails console
User.where(status: 'active').explain

# Look for "Seq Scan" - indicates missing index
# Should see "Index Scan" or "Index Only Scan"
```

---

## 5. Callbacks Anti-Patterns

### Callback Hell

```ruby
# WRONG - too many callbacks, hard to reason about
class Order < ApplicationRecord
  after_create :send_confirmation_email
  after_create :notify_warehouse
  after_create :update_inventory
  after_create :charge_payment
  after_create :create_invoice
  after_create :log_analytics
  after_update :sync_to_external_system
  after_destroy :refund_payment
end

# CORRECT - use service objects for complex workflows
class Order < ApplicationRecord
  # Only simple, always-needed callbacks
  after_create :set_order_number

  private

  def set_order_number
    update_column(:number, "ORD-#{id.to_s.rjust(8, '0')}")
  end
end

# Service object handles the workflow
class OrderCreationService
  def initialize(order, user:)
    @order = order
    @user = user
  end

  def call
    ActiveRecord::Base.transaction do
      @order.save!
      charge_payment
      update_inventory
      create_invoice
    end

    # Non-critical async tasks
    OrderConfirmationMailer.confirm(@order).deliver_later
    WarehouseNotifier.new(@order).notify_async
    Analytics.track('order_created', order_id: @order.id)

    @order
  rescue PaymentError => e
    @order.errors.add(:base, e.message)
    false
  end
end
```

### Hidden Callbacks

```ruby
# WRONG - callbacks on associated models cause surprises
class User < ApplicationRecord
  has_many :posts, dependent: :destroy
end

class Post < ApplicationRecord
  after_destroy :notify_author  # Called when user is destroyed!
end

# CORRECT - be explicit about cascade behavior
class User < ApplicationRecord
  has_many :posts, dependent: :delete_all  # Skips callbacks, faster
end

# Or handle in service
class UserDeletionService
  def call(user)
    user.posts.update_all(author_id: nil)  # Anonymize instead
    user.destroy
  end
end
```

---

## 6. Transaction Pitfalls

### Nested Transaction Mistakes

```ruby
# WRONG - nested transaction doesn't work as expected
def transfer_funds(from, to, amount)
  ActiveRecord::Base.transaction do
    from.withdraw(amount)

    ActiveRecord::Base.transaction do  # This is JOINED to outer transaction!
      to.deposit(amount)
    end
  end
end

# CORRECT - use requires_new for true nested transaction
def transfer_funds(from, to, amount)
  ActiveRecord::Base.transaction do
    from.withdraw(amount)

    ActiveRecord::Base.transaction(requires_new: true) do
      to.deposit(amount)
    end
  end
end
```

### After Commit Timing

```ruby
# WRONG - job enqueued inside transaction, but record might not exist yet
class Order < ApplicationRecord
  after_create :enqueue_processing

  def enqueue_processing
    ProcessOrderJob.perform_later(id)  # Job might run before commit!
  end
end

# CORRECT - use after_commit
class Order < ApplicationRecord
  after_commit :enqueue_processing, on: :create

  def enqueue_processing
    ProcessOrderJob.perform_later(id)
  end
end
```

---

## 7. Memory Bloat

### String Concatenation in Loops

```ruby
# WRONG - creates many string objects
result = ""
users.each do |user|
  result += "#{user.name}\n"  # Creates new string each iteration
end

# CORRECT - use array and join
lines = users.map { |user| user.name }
result = lines.join("\n")

# CORRECT - use StringIO for large outputs
require 'stringio'
output = StringIO.new
users.find_each do |user|
  output.puts user.name
end
result = output.string
```

### Pluck vs Select

```ruby
# WRONG - loads full ActiveRecord objects just for one column
emails = User.all.map(&:email)

# CORRECT - pluck returns just the values
emails = User.pluck(:email)

# CORRECT - select if you need multiple columns but not full objects
User.select(:id, :email, :name).find_each do |user|
  # Lightweight object with only selected attributes
end
```

---

## 8. Time Zone Bugs

```ruby
# WRONG - uses system time, ignores Rails time zone
Time.now
Date.today
DateTime.now

# CORRECT - use Rails time helpers
Time.current
Time.zone.today
DateTime.current

# WRONG - parsing without time zone
Time.parse("2024-01-15 10:00:00")

# CORRECT - parse in time zone
Time.zone.parse("2024-01-15 10:00:00")

# WRONG - comparing with different time zones
if record.created_at > Time.now  # System time vs UTC

# CORRECT
if record.created_at > Time.current

# Database queries - always use Time.current
User.where("created_at > ?", Time.current)
User.where("created_at > ?", 1.day.ago)
```

### Time Zone Configuration

```ruby
# config/application.rb
config.time_zone = 'Eastern Time (US & Canada)'
config.active_record.default_timezone = :utc  # Store as UTC
```

---

## 9. Enum Pitfalls

```ruby
# WRONG - adding values in the middle breaks existing data
class Order < ApplicationRecord
  enum :status, { pending: 0, shipped: 1, delivered: 2 }
end

# Later, someone adds:
enum :status, { pending: 0, processing: 1, shipped: 2, delivered: 3 }  # BREAKS!

# CORRECT - use explicit values, add at end
class Order < ApplicationRecord
  enum :status, {
    pending: 0,
    shipped: 1,
    delivered: 2,
    processing: 3,  # Added at end with new value
    cancelled: 4
  }
end

# CORRECT - use string enum for safety (Rails 7+)
class Order < ApplicationRecord
  enum :status, {
    pending: "pending",
    processing: "processing",
    shipped: "shipped",
    delivered: "delivered"
  }
end
```

---

## 10. Validation Bypass

```ruby
# These methods SKIP validations - use carefully
user.update_attribute(:name, "New Name")
user.update_column(:name, "New Name")
user.update_columns(name: "New Name")
User.update_all(status: "active")
user.save(validate: false)
user.toggle!(:active)
user.increment!(:views_count)
user.decrement!(:credits)
user.touch

# These methods RUN validations
user.update(name: "New Name")
user.update!(name: "New Name")  # Raises on failure
user.save
user.save!
```

---

## 11. Scope vs Class Method

```ruby
# WRONG - scope returns nil on empty result, breaks chaining
scope :recent, -> { where("created_at > ?", 1.week.ago) if some_condition }

# If some_condition is false, returns nil, breaking: Post.recent.published

# CORRECT - scopes should always return a relation
scope :recent, -> {
  if some_condition
    where("created_at > ?", 1.week.ago)
  else
    all  # Returns empty scope, allows chaining
  end
}

# CORRECT - use class method for conditional logic
def self.recent
  return all unless some_condition
  where("created_at > ?", 1.week.ago)
end
```

---

## 12. Uniqueness Race Condition

```ruby
# WRONG - race condition possible
validates :email, uniqueness: true

# Two requests can pass validation, then one INSERT fails

# CORRECT - add database constraint
add_index :users, :email, unique: true

# Handle the database error
def create
  @user = User.new(user_params)
  @user.save!
rescue ActiveRecord::RecordNotUnique
  @user.errors.add(:email, :taken)
  render :new
end
```

---

## 13. Delete vs Destroy

```ruby
# destroy - runs callbacks and dependent destroys
user.destroy       # Slow, runs all callbacks
User.destroy_all   # Very slow on large datasets

# delete - direct SQL, skips callbacks
user.delete        # Fast, no callbacks
User.delete_all    # Fast, but skips ALL callbacks

# Choose based on need
class User < ApplicationRecord
  has_many :posts, dependent: :destroy    # Need callbacks
  has_many :sessions, dependent: :delete_all  # Speed over callbacks
end
```

---

## Quick Reference

| Problem | Solution |
|---------|----------|
| N+1 queries | `includes`, `preload`, `eager_load` |
| Counting in loops | Counter cache column |
| Loading all records | `find_each`, `find_in_batches` |
| Slow queries | Add indexes, check with `explain` |
| Complex callbacks | Service objects |
| Job timing issues | `after_commit` not `after_create` |
| Memory bloat | `pluck` instead of `map` |
| Time zone bugs | `Time.current` not `Time.now` |
| Enum changes | Explicit values, add at end only |
| Validation bypass | Know which methods skip validations |
| Race conditions | Database unique constraints |
| Slow deletes | `delete_all` when callbacks not needed |
