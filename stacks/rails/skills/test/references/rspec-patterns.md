# RSpec Test Patterns

Reference patterns for writing RSpec tests in a Rails application. All specs follow
these conventions.

## General Rules

- `frozen_string_literal: true` on all spec files
- `require 'rails_helper'` at the top of every spec
- Use `described_class` instead of repeating the class name
- Use `subject` for the primary object under test
- One logical assertion per `it` block
- Descriptive `describe` and `context` blocks
- `let` for lazy evaluation, `let!` for eager creation
- `build` for objects that do not need to be persisted, `create` for persisted

---

## Model Spec Pattern

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Profile, type: :model do
  subject(:profile) { build(:profile) }

  # -- Associations --
  describe 'associations' do
    it { is_expected.to belong_to(:user) }
    it { is_expected.to belong_to(:company).optional }
    it { is_expected.to have_many(:experiences).dependent(:destroy) }
    it { is_expected.to have_many(:skills).through(:profile_skills) }
    it { is_expected.to have_one(:resume).dependent(:destroy) }
  end

  # -- Validations --
  describe 'validations' do
    it { is_expected.to validate_presence_of(:name) }
    it { is_expected.to validate_presence_of(:email) }
    it { is_expected.to validate_uniqueness_of(:email).case_insensitive }
    it { is_expected.to validate_length_of(:name).is_at_most(255) }
    it { is_expected.to validate_length_of(:bio).is_at_most(5000) }
    it { is_expected.to validate_inclusion_of(:status).in_array(%w[active inactive archived]) }
  end

  # -- Enums --
  describe 'enums' do
    it { is_expected.to define_enum_for(:role).with_values(member: 0, admin: 1, owner: 2) }
  end

  # -- Scopes --
  describe 'scopes' do
    describe '.active' do
      it 'returns only active profiles' do
        active_profile = create(:profile, active: true)
        create(:profile, active: false)

        expect(described_class.active).to contain_exactly(active_profile)
      end
    end

    describe '.recent' do
      it 'orders by created_at descending' do
        old_profile = create(:profile, created_at: 2.days.ago)
        new_profile = create(:profile, created_at: 1.hour.ago)

        expect(described_class.recent).to eq([new_profile, old_profile])
      end
    end

    describe '.search' do
      it 'finds profiles by name (case-insensitive)' do
        matching = create(:profile, name: 'Jane Developer')
        create(:profile, name: 'Bob Manager')

        expect(described_class.search('jane')).to contain_exactly(matching)
      end
    end
  end

  # -- Callbacks --
  describe 'callbacks' do
    describe '#normalize_email' do
      it 'downcases and strips email before validation' do
        profile = build(:profile, email: '  USER@EXAMPLE.COM  ')
        profile.valid?

        expect(profile.email).to eq('user@example.com')
      end
    end

    describe '#send_welcome_notification' do
      it 'enqueues a notification job after creation' do
        expect {
          create(:profile)
        }.to have_enqueued_job(NotificationJob)
      end
    end
  end

  # -- Instance Methods --
  describe '#full_name' do
    it 'returns first and last name combined' do
      profile = build(:profile, first_name: 'Jane', last_name: 'Doe')

      expect(profile.full_name).to eq('Jane Doe')
    end
  end
end
```

---

## Request Spec Pattern

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'Profiles API', type: :request do
  let(:user) { create(:user) }
  let(:headers) { auth_headers_for(user) }

  # -- INDEX --
  describe 'GET /api/v1/profiles' do
    context 'when authenticated' do
      let!(:profiles) { create_list(:profile, 3, user:) }

      it 'returns a paginated list of profiles' do
        get '/api/v1/profiles', headers:

        expect(response).to have_http_status(:ok)
        expect(json_response['profiles'].size).to eq(3)
        expect(json_response).to have_key('meta')
      end

      it 'paginates results' do
        get '/api/v1/profiles', params: { page: 1, per_page: 2 }, headers:

        expect(json_response['profiles'].size).to eq(2)
        expect(json_response['meta']['total_count']).to eq(3)
      end
    end

    context 'when unauthenticated' do
      it 'returns 401 unauthorized' do
        get '/api/v1/profiles'

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  # -- SHOW --
  describe 'GET /api/v1/profiles/:id' do
    let(:profile) { create(:profile, user:) }

    context 'when the profile exists' do
      it 'returns the profile' do
        get "/api/v1/profiles/#{profile.id}", headers:

        expect(response).to have_http_status(:ok)
        expect(json_response['id']).to eq(profile.id)
        expect(json_response['name']).to eq(profile.name)
      end
    end

    context 'when the profile does not exist' do
      it 'returns 404 not found' do
        get '/api/v1/profiles/99999', headers:

        expect(response).to have_http_status(:not_found)
      end
    end
  end

  # -- CREATE --
  describe 'POST /api/v1/profiles' do
    let(:valid_params) do
      {
        profile: {
          name: 'Jane Doe',
          email: 'jane@example.com',
          bio: 'Senior engineer'
        }
      }
    end

    context 'with valid params' do
      it 'creates a new profile' do
        expect {
          post '/api/v1/profiles', params: valid_params, headers:
        }.to change(Profile, :count).by(1)
      end

      it 'returns the created profile' do
        post '/api/v1/profiles', params: valid_params, headers:

        expect(response).to have_http_status(:created)
        expect(json_response['name']).to eq('Jane Doe')
      end
    end

    context 'with invalid params' do
      let(:invalid_params) { { profile: { name: '', email: '' } } }

      it 'does not create a profile' do
        expect {
          post '/api/v1/profiles', params: invalid_params, headers:
        }.not_to change(Profile, :count)
      end

      it 'returns validation errors' do
        post '/api/v1/profiles', params: invalid_params, headers:

        expect(response).to have_http_status(:unprocessable_entity)
        expect(json_response['errors']).to be_present
      end
    end
  end

  # -- UPDATE --
  describe 'PATCH /api/v1/profiles/:id' do
    let(:profile) { create(:profile, user:) }

    context 'with valid params' do
      it 'updates the profile' do
        patch "/api/v1/profiles/#{profile.id}",
              params: { profile: { name: 'Updated Name' } },
              headers:

        expect(response).to have_http_status(:ok)
        expect(profile.reload.name).to eq('Updated Name')
      end
    end

    context 'when not the owner' do
      let(:other_user) { create(:user) }
      let(:other_headers) { auth_headers_for(other_user) }

      it 'returns 403 forbidden' do
        patch "/api/v1/profiles/#{profile.id}",
              params: { profile: { name: 'Hacked' } },
              headers: other_headers

        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  # -- DELETE --
  describe 'DELETE /api/v1/profiles/:id' do
    let!(:profile) { create(:profile, user:) }

    it 'deletes the profile' do
      expect {
        delete "/api/v1/profiles/#{profile.id}", headers:
      }.to change(Profile, :count).by(-1)
    end

    it 'returns no content' do
      delete "/api/v1/profiles/#{profile.id}", headers:

      expect(response).to have_http_status(:no_content)
    end
  end
end
```

---

## Service Spec Pattern

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BulkImport::ProfilesService do
  subject(:service) { described_class.new(file:, user:) }

  let(:user) { create(:user, :admin) }
  let(:file) { fixture_file_upload('profiles.csv', 'text/csv') }

  describe '#call' do
    context 'when the file is valid' do
      it 'creates profiles from the CSV' do
        expect { service.call }.to change(Profile, :count).by(3)
      end

      it 'returns a success result' do
        result = service.call

        expect(result).to be_success
        expect(result.imported_count).to eq(3)
      end

      it 'associates profiles with the importing user' do
        service.call

        expect(Profile.last.imported_by).to eq(user)
      end
    end

    context 'when the file has invalid rows' do
      let(:file) { fixture_file_upload('profiles_with_errors.csv', 'text/csv') }

      it 'imports valid rows and collects errors' do
        result = service.call

        expect(result.imported_count).to eq(2)
        expect(result.errors).to include(match(/Row 3: Email is invalid/))
      end
    end

    context 'when the file is empty' do
      let(:file) { fixture_file_upload('empty.csv', 'text/csv') }

      it 'returns an error result' do
        result = service.call

        expect(result).to be_failure
        expect(result.errors).to include('File is empty')
      end
    end

    context 'when the user is not authorized' do
      let(:user) { create(:user) }

      it 'raises an authorization error' do
        expect { service.call }.to raise_error(Pundit::NotAuthorizedError)
      end
    end
  end
end
```

---

## Job Spec Pattern

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Sync::AirtableImportJob, type: :job do
  subject(:job) { described_class }

  describe '#perform' do
    let(:import) { create(:import, :pending) }

    it 'calls the import service' do
      service = instance_double(Sync::AirtableImportService, call: true)
      allow(Sync::AirtableImportService).to receive(:new)
        .with(import:)
        .and_return(service)

      job.perform_now(import.id)

      expect(service).to have_received(:call)
    end

    context 'when the import is already completed' do
      let(:import) { create(:import, :completed) }

      it 'does not process the import' do
        expect(Sync::AirtableImportService).not_to receive(:new)

        job.perform_now(import.id)
      end
    end

    context 'when the import record does not exist' do
      it 'handles the error gracefully' do
        expect {
          job.perform_now(99999)
        }.not_to raise_error
      end
    end
  end

  describe 'queue configuration' do
    it 'is enqueued in the default queue' do
      expect(described_class.new.queue_name).to eq('default')
    end
  end
end
```

---

## Shared Examples Pattern

```ruby
# spec/support/shared_examples/authenticatable.rb
# frozen_string_literal: true

RSpec.shared_examples 'an authenticated endpoint' do |method, path|
  it 'returns 401 when unauthenticated' do
    send(method, path)

    expect(response).to have_http_status(:unauthorized)
  end
end

# Usage in specs:
it_behaves_like 'an authenticated endpoint', :get, '/api/v1/profiles'
```

---

## Spec Helpers

```ruby
# spec/support/json_helpers.rb
# frozen_string_literal: true

module JsonHelpers
  def json_response
    JSON.parse(response.body)
  end
end

RSpec.configure do |config|
  config.include JsonHelpers, type: :request
end
```

```ruby
# spec/support/auth_helpers.rb
# frozen_string_literal: true

module AuthHelpers
  def auth_headers_for(user)
    token = JsonWebToken.encode(user_id: user.id)
    { 'Authorization' => "Bearer #{token}" }
  end
end

RSpec.configure do |config|
  config.include AuthHelpers, type: :request
end
```
