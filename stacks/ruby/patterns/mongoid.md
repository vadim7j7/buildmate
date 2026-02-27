# Mongoid (MongoDB ODM) Patterns

## Model Definition

```ruby
# app/models/user.rb
class User
  include Mongoid::Document
  include Mongoid::Timestamps

  # Fields
  field :email, type: String
  field :name, type: String
  field :role, type: String, default: 'user'
  field :settings, type: Hash, default: {}
  field :tags, type: Array, default: []

  # Indexes
  index({ email: 1 }, { unique: true })
  index({ role: 1 })
  index({ created_at: -1 })

  # Validations
  validates :email, presence: true, uniqueness: true
  validates :name, presence: true

  # Associations
  has_many :posts, dependent: :destroy
  belongs_to :organization, optional: true
  embeds_many :addresses
  embeds_one :profile

  # Scopes
  scope :admins, -> { where(role: 'admin') }
  scope :recent, -> { order(created_at: :desc) }
end
```

## Embedded Documents

```ruby
# app/models/address.rb
class Address
  include Mongoid::Document

  field :street, type: String
  field :city, type: String
  field :zip, type: String
  field :primary, type: Boolean, default: false

  embedded_in :user

  validates :street, :city, :zip, presence: true
end

# Usage
user.addresses.create!(street: '123 Main', city: 'NYC', zip: '10001')
user.addresses.where(primary: true).first
```

## Querying

```ruby
# Basic queries
User.where(role: 'admin')
User.where(:created_at.gte => 1.week.ago)
User.where(:tags.in => ['ruby'])

# Embedded document queries
User.where('addresses.city' => 'NYC')

# Complex queries
User.where(role: 'user')
    .where(:created_at.gte => 1.month.ago)
    .order(created_at: :desc)
    .limit(10)

# Aggregation pipeline
User.collection.aggregate([
  { '$match' => { role: 'user' } },
  { '$group' => { _id: '$organization_id', count: { '$sum' => 1 } } },
  { '$sort' => { count: -1 } }
])
```

## Callbacks

```ruby
class User
  include Mongoid::Document

  before_save :normalize_email
  after_create :send_welcome_email

  private

  def normalize_email
    self.email = email.downcase.strip
  end

  def send_welcome_email
    UserMailer.welcome(self).deliver_later
  end
end
```

## Many-to-Many with Arrays

```ruby
# Using array of IDs (simpler, good for small sets)
class User
  include Mongoid::Document

  field :role_ids, type: Array, default: []

  def roles
    Role.where(:_id.in => role_ids)
  end

  def add_role(role)
    role_ids << role.id unless role_ids.include?(role.id)
    save
  end
end
```

## Configuration

```yaml
# config/mongoid.yml
development:
  clients:
    default:
      database: myapp_development
      hosts:
        - localhost:27017
      options:
        server_selection_timeout: 5

production:
  clients:
    default:
      uri: <%= ENV['MONGODB_URI'] %>
      options:
        server_selection_timeout: 5
        max_pool_size: 10
```

## Key Differences from ActiveRecord

| ActiveRecord | Mongoid |
|--------------|---------|
| `has_many through:` | Use arrays or embedded docs |
| `joins` | Not available, use `$lookup` aggregation |
| Migrations | Not needed, schema-less |
| `find_by` | `find_by` works the same |
| `where(id: ids)` | `where(:_id.in => ids)` |
| Integer IDs | ObjectId by default |

## Key Rules

1. Index frequently queried fields
2. Use embedded documents for 1:1 and 1:few relationships
3. Use references (belongs_to/has_many) for 1:many with large sets
4. Use arrays for small many-to-many relationships
5. Prefer `$in` queries over multiple lookups
6. Use aggregation pipeline for complex queries
