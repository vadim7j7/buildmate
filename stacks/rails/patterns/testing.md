# Rails Testing Patterns

Testing patterns and conventions for Ruby on Rails applications using RSpec.
All agents must follow these patterns when writing tests.

---

## 1. Test File Organization

```
spec/
├── models/           # Model unit tests
├── services/         # Service object tests
├── controllers/      # Controller tests (request specs preferred)
├── requests/         # API/request specs (preferred over controller specs)
├── jobs/             # Background job tests
├── mailers/          # Mailer tests
├── policies/         # Pundit policy tests
├── presenters/       # Presenter tests
├── support/          # Shared helpers and configurations
│   ├── factory_bot.rb
│   ├── database_cleaner.rb
│   └── shared_examples/
├── factories/        # FactoryBot factories
├── fixtures/         # File fixtures (not ActiveRecord fixtures)
│   └── files/
├── rails_helper.rb
└── spec_helper.rb
```

---

## 2. Model Specs

Test validations, associations, scopes, and instance methods.

```ruby
# spec/models/user_spec.rb
require 'rails_helper'

RSpec.describe User, type: :model do
  describe 'validations' do
    it { is_expected.to validate_presence_of(:email) }
    it { is_expected.to validate_uniqueness_of(:email).case_insensitive }
    it { is_expected.to validate_length_of(:password).is_at_least(12) }

    # Custom validation
    describe '#email_domain_allowed' do
      it 'rejects disposable email domains' do
        user = build(:user, email: 'test@tempmail.com')
        expect(user).not_to be_valid
        expect(user.errors[:email]).to include('domain not allowed')
      end
    end
  end

  describe 'associations' do
    it { is_expected.to belong_to(:organization) }
    it { is_expected.to have_many(:posts).dependent(:destroy) }
    it { is_expected.to have_many(:comments).through(:posts) }
    it { is_expected.to have_one_attached(:avatar) }
  end

  describe 'scopes' do
    describe '.active' do
      it 'returns only active users' do
        active_user = create(:user, active: true)
        inactive_user = create(:user, active: false)

        expect(User.active).to include(active_user)
        expect(User.active).not_to include(inactive_user)
      end
    end

    describe '.created_after' do
      it 'returns users created after the given date' do
        old_user = create(:user, created_at: 1.month.ago)
        new_user = create(:user, created_at: 1.day.ago)

        expect(User.created_after(1.week.ago)).to eq([new_user])
      end
    end
  end

  describe '#full_name' do
    it 'combines first and last name' do
      user = build(:user, first_name: 'John', last_name: 'Doe')
      expect(user.full_name).to eq('John Doe')
    end

    it 'handles missing last name' do
      user = build(:user, first_name: 'John', last_name: nil)
      expect(user.full_name).to eq('John')
    end
  end

  describe '#admin?' do
    it 'returns true for admin role' do
      user = build(:user, role: :admin)
      expect(user).to be_admin
    end

    it 'returns false for member role' do
      user = build(:user, role: :member)
      expect(user).not_to be_admin
    end
  end
end
```

---

## 3. Request Specs

Preferred over controller specs. Test full request/response cycle.

```ruby
# spec/requests/api/v1/posts_spec.rb
require 'rails_helper'

RSpec.describe 'Posts API', type: :request do
  let(:user) { create(:user) }
  let(:headers) { { 'Authorization' => "Bearer #{user.api_token}" } }

  describe 'GET /api/v1/posts' do
    it 'returns paginated posts' do
      create_list(:post, 25, user: user)

      get '/api/v1/posts', headers: headers, params: { page: 1, per_page: 10 }

      expect(response).to have_http_status(:ok)
      expect(json_response['data'].length).to eq(10)
      expect(json_response['meta']['total']).to eq(25)
      expect(json_response['meta']['page']).to eq(1)
    end

    it 'filters by status' do
      published = create(:post, user: user, status: :published)
      draft = create(:post, user: user, status: :draft)

      get '/api/v1/posts', headers: headers, params: { status: 'published' }

      expect(json_response['data'].pluck('id')).to eq([published.id])
    end

    context 'without authentication' do
      it 'returns 401 unauthorized' do
        get '/api/v1/posts'

        expect(response).to have_http_status(:unauthorized)
        expect(json_response['error']).to eq('Authentication required')
      end
    end
  end

  describe 'POST /api/v1/posts' do
    let(:valid_params) do
      {
        post: {
          title: 'New Post',
          body: 'Post content here',
          status: 'draft'
        }
      }
    end

    it 'creates a post' do
      expect {
        post '/api/v1/posts', headers: headers, params: valid_params
      }.to change(Post, :count).by(1)

      expect(response).to have_http_status(:created)
      expect(json_response['data']['title']).to eq('New Post')
    end

    it 'returns validation errors for invalid data' do
      post '/api/v1/posts', headers: headers, params: { post: { title: '' } }

      expect(response).to have_http_status(:unprocessable_entity)
      expect(json_response['errors']).to include("Title can't be blank")
    end
  end

  describe 'PUT /api/v1/posts/:id' do
    let(:post_record) { create(:post, user: user) }

    it 'updates the post' do
      put "/api/v1/posts/#{post_record.id}",
          headers: headers,
          params: { post: { title: 'Updated Title' } }

      expect(response).to have_http_status(:ok)
      expect(post_record.reload.title).to eq('Updated Title')
    end

    context 'when post belongs to another user' do
      let(:other_post) { create(:post) }

      it 'returns 403 forbidden' do
        put "/api/v1/posts/#{other_post.id}",
            headers: headers,
            params: { post: { title: 'Hacked' } }

        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe 'DELETE /api/v1/posts/:id' do
    let!(:post_record) { create(:post, user: user) }

    it 'deletes the post' do
      expect {
        delete "/api/v1/posts/#{post_record.id}", headers: headers
      }.to change(Post, :count).by(-1)

      expect(response).to have_http_status(:no_content)
    end
  end

  private

  def json_response
    JSON.parse(response.body)
  end
end
```

---

## 4. Service Object Specs

```ruby
# spec/services/order_creation_service_spec.rb
require 'rails_helper'

RSpec.describe OrderCreationService do
  subject(:service) { described_class.new(cart, user: user) }

  let(:user) { create(:user) }
  let(:cart) { create(:cart, :with_items, user: user) }

  describe '#call' do
    context 'with valid cart' do
      it 'creates an order' do
        expect { service.call }.to change(Order, :count).by(1)
      end

      it 'returns the created order' do
        result = service.call
        expect(result).to be_a(Order)
        expect(result).to be_persisted
      end

      it 'transfers cart items to order items' do
        order = service.call
        expect(order.line_items.count).to eq(cart.items.count)
      end

      it 'clears the cart' do
        service.call
        expect(cart.reload.items).to be_empty
      end

      it 'sends confirmation email' do
        expect {
          service.call
        }.to have_enqueued_mail(OrderMailer, :confirmation).with(a_kind_of(Order))
      end
    end

    context 'with empty cart' do
      let(:cart) { create(:cart, user: user) }

      it 'returns nil' do
        expect(service.call).to be_nil
      end

      it 'does not create an order' do
        expect { service.call }.not_to change(Order, :count)
      end
    end

    context 'when payment fails' do
      before do
        allow(PaymentGateway).to receive(:charge).and_raise(PaymentError, 'Card declined')
      end

      it 'rolls back the transaction' do
        expect { service.call }.to raise_error(PaymentError)
        expect(Order.count).to eq(0)
      end
    end
  end
end
```

---

## 5. Job Specs

```ruby
# spec/jobs/send_weekly_digest_job_spec.rb
require 'rails_helper'

RSpec.describe SendWeeklyDigestJob, type: :job do
  describe '#perform' do
    let(:user) { create(:user, digest_enabled: true) }

    it 'sends digest email to user' do
      expect {
        described_class.perform_now(user.id)
      }.to have_enqueued_mail(DigestMailer, :weekly).with(user)
    end

    context 'when user has digest disabled' do
      let(:user) { create(:user, digest_enabled: false) }

      it 'does not send email' do
        expect {
          described_class.perform_now(user.id)
        }.not_to have_enqueued_mail
      end
    end

    context 'when user does not exist' do
      it 'does not raise error' do
        expect {
          described_class.perform_now(-1)
        }.not_to raise_error
      end
    end
  end

  describe 'job configuration' do
    it 'is enqueued in the mailers queue' do
      expect(described_class.queue_name).to eq('mailers')
    end

    it 'retries on failure' do
      expect(described_class.retry_on).to include(Net::OpenTimeout)
    end
  end
end
```

---

## 6. Factory Patterns

```ruby
# spec/factories/users.rb
FactoryBot.define do
  factory :user do
    sequence(:email) { |n| "user#{n}@example.com" }
    first_name { 'John' }
    last_name { 'Doe' }
    password { 'SecurePassword123!' }
    role { :member }

    trait :admin do
      role { :admin }
    end

    trait :with_avatar do
      after(:create) do |user|
        user.avatar.attach(
          io: File.open(Rails.root.join('spec/fixtures/files/avatar.jpg')),
          filename: 'avatar.jpg',
          content_type: 'image/jpeg'
        )
      end
    end

    trait :with_posts do
      transient do
        posts_count { 3 }
      end

      after(:create) do |user, evaluator|
        create_list(:post, evaluator.posts_count, user: user)
      end
    end
  end
end

# spec/factories/posts.rb
FactoryBot.define do
  factory :post do
    association :user
    sequence(:title) { |n| "Post Title #{n}" }
    body { 'Post body content' }
    status { :draft }

    trait :published do
      status { :published }
      published_at { Time.current }
    end

    trait :with_comments do
      transient do
        comments_count { 5 }
      end

      after(:create) do |post, evaluator|
        create_list(:comment, evaluator.comments_count, post: post)
      end
    end
  end
end
```

### Factory Usage

```ruby
# Basic usage
user = create(:user)
user = build(:user)  # Not persisted

# With traits
admin = create(:user, :admin)
user_with_posts = create(:user, :with_posts, posts_count: 5)

# Overriding attributes
user = create(:user, email: 'custom@example.com')

# Lists
users = create_list(:user, 10)
users = create_list(:user, 5, :admin)
```

---

## 7. Shared Examples

```ruby
# spec/support/shared_examples/api_authentication.rb
RSpec.shared_examples 'requires authentication' do
  context 'without authentication header' do
    let(:headers) { {} }

    it 'returns 401 unauthorized' do
      make_request
      expect(response).to have_http_status(:unauthorized)
    end
  end

  context 'with invalid token' do
    let(:headers) { { 'Authorization' => 'Bearer invalid' } }

    it 'returns 401 unauthorized' do
      make_request
      expect(response).to have_http_status(:unauthorized)
    end
  end
end

# Usage
RSpec.describe 'Posts API' do
  describe 'GET /api/v1/posts' do
    it_behaves_like 'requires authentication' do
      let(:make_request) { get '/api/v1/posts', headers: headers }
    end
  end
end
```

```ruby
# spec/support/shared_examples/soft_deletable.rb
RSpec.shared_examples 'soft deletable' do
  describe '#soft_delete' do
    it 'sets deleted_at timestamp' do
      expect { subject.soft_delete }.to change { subject.deleted_at }.from(nil)
    end

    it 'excludes from default scope' do
      subject.soft_delete
      expect(described_class.all).not_to include(subject)
    end
  end

  describe '.with_deleted' do
    it 'includes soft-deleted records' do
      subject.soft_delete
      expect(described_class.with_deleted).to include(subject)
    end
  end
end

# Usage
RSpec.describe Post do
  subject { create(:post) }
  it_behaves_like 'soft deletable'
end
```

---

## 8. Mocking and Stubbing

```ruby
# Stub external API calls
RSpec.describe PaymentService do
  describe '#charge' do
    it 'charges the card via Stripe' do
      allow(Stripe::Charge).to receive(:create).and_return(
        OpenStruct.new(id: 'ch_123', status: 'succeeded')
      )

      result = described_class.new.charge(amount: 1000, source: 'tok_visa')

      expect(Stripe::Charge).to have_received(:create).with(
        amount: 1000,
        currency: 'usd',
        source: 'tok_visa'
      )
      expect(result.status).to eq('succeeded')
    end
  end
end

# Use WebMock for HTTP requests
require 'webmock/rspec'

RSpec.describe ExternalApiClient do
  before do
    stub_request(:get, 'https://api.example.com/users')
      .to_return(
        status: 200,
        body: [{ id: 1, name: 'John' }].to_json,
        headers: { 'Content-Type' => 'application/json' }
      )
  end

  it 'fetches users from external API' do
    users = described_class.new.fetch_users
    expect(users.first['name']).to eq('John')
  end
end

# Use VCR for recording HTTP interactions
VCR.configure do |config|
  config.cassette_library_dir = 'spec/cassettes'
  config.hook_into :webmock
  config.configure_rspec_metadata!
end

RSpec.describe 'External API', :vcr do
  it 'records and replays HTTP interactions' do
    # First run: records to spec/cassettes/external_api.yml
    # Subsequent runs: replays from cassette
    result = ExternalApiClient.new.fetch_data
    expect(result).to be_present
  end
end
```

---

## 9. Testing Time

```ruby
# Freeze time for predictable tests
RSpec.describe Subscription do
  describe '#expired?' do
    it 'returns true when past expiration date' do
      subscription = create(:subscription, expires_at: 1.day.from_now)

      travel_to 2.days.from_now do
        expect(subscription).to be_expired
      end
    end

    it 'returns false when before expiration date' do
      subscription = create(:subscription, expires_at: 1.day.from_now)

      travel_to 1.hour.from_now do
        expect(subscription).not_to be_expired
      end
    end
  end
end

# Freeze at specific time
RSpec.describe Report do
  around do |example|
    travel_to Time.zone.local(2024, 1, 15, 10, 30, 0) do
      example.run
    end
  end

  it 'generates report for current month' do
    report = described_class.monthly
    expect(report.period).to eq('January 2024')
  end
end
```

---

## 10. Database Cleaning

```ruby
# spec/support/database_cleaner.rb
RSpec.configure do |config|
  config.before(:suite) do
    DatabaseCleaner.clean_with(:truncation)
  end

  config.before(:each) do
    DatabaseCleaner.strategy = :transaction
  end

  config.before(:each, js: true) do
    DatabaseCleaner.strategy = :truncation
  end

  config.before(:each) do
    DatabaseCleaner.start
  end

  config.after(:each) do
    DatabaseCleaner.clean
  end
end
```

---

## 11. Test Helpers

```ruby
# spec/support/api_helpers.rb
module ApiHelpers
  def json_response
    JSON.parse(response.body, symbolize_names: true)
  end

  def auth_headers(user)
    { 'Authorization' => "Bearer #{user.api_token}" }
  end

  def expect_json_schema(schema_name)
    expect(response).to match_json_schema(schema_name)
  end
end

RSpec.configure do |config|
  config.include ApiHelpers, type: :request
end
```

---

## Quick Reference

| Test Type | Location | Purpose |
|-----------|----------|---------|
| Model specs | `spec/models/` | Validations, scopes, methods |
| Request specs | `spec/requests/` | API endpoints, full request cycle |
| Service specs | `spec/services/` | Business logic |
| Job specs | `spec/jobs/` | Background jobs |
| Mailer specs | `spec/mailers/` | Email generation |
| Policy specs | `spec/policies/` | Authorization |

### Matchers Cheat Sheet

```ruby
# Shoulda matchers
it { is_expected.to validate_presence_of(:name) }
it { is_expected.to belong_to(:user) }
it { is_expected.to have_many(:comments) }

# Change matchers
expect { action }.to change(Model, :count).by(1)
expect { action }.to change { object.attribute }.from(old).to(new)

# Job matchers
expect { action }.to have_enqueued_job(MyJob)
expect { action }.to have_enqueued_mail(MyMailer, :method_name)

# Response matchers
expect(response).to have_http_status(:ok)
expect(response).to redirect_to(path)
```
