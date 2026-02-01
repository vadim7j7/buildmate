# RSpec Spec Examples

Complete spec examples for each type of class in the Rails application.

---

## Model Spec Example

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Profile, type: :model do
  subject(:profile) { build(:profile) }

  describe 'associations' do
    it { is_expected.to belong_to(:user) }
    it { is_expected.to belong_to(:company).optional }
    it { is_expected.to have_many(:experiences).dependent(:destroy) }
    it { is_expected.to have_many(:skills).through(:profile_skills) }
  end

  describe 'validations' do
    it { is_expected.to validate_presence_of(:name) }
    it { is_expected.to validate_presence_of(:email) }
    it { is_expected.to validate_uniqueness_of(:email).case_insensitive }
    it { is_expected.to validate_length_of(:name).is_at_most(255) }
  end

  describe 'enums' do
    it { is_expected.to define_enum_for(:status).with_values(active: 0, inactive: 1, archived: 2) }
  end

  describe 'scopes' do
    describe '.active' do
      it 'returns only active profiles' do
        active = create(:profile, status: :active)
        create(:profile, status: :inactive)

        expect(described_class.active).to contain_exactly(active)
      end
    end

    describe '.search' do
      it 'finds profiles by name (case-insensitive)' do
        matching = create(:profile, name: 'Jane Developer')
        create(:profile, name: 'Bob Manager')

        expect(described_class.search('jane')).to contain_exactly(matching)
      end

      it 'returns all when query is blank' do
        profiles = create_list(:profile, 3)

        expect(described_class.search(nil)).to match_array(profiles)
      end
    end
  end

  describe 'callbacks' do
    describe '#normalize_email' do
      it 'downcases and strips email' do
        profile = build(:profile, email: '  USER@EXAMPLE.COM  ')
        profile.valid?

        expect(profile.email).to eq('user@example.com')
      end
    end
  end

  describe '#display_name' do
    context 'when profile has a company' do
      it 'includes the company name' do
        company = build(:company, name: 'Acme Corp')
        profile = build(:profile, name: 'Jane', company:)

        expect(profile.display_name).to eq('Jane (Acme Corp)')
      end
    end

    context 'when profile has no company' do
      it 'returns just the name' do
        profile = build(:profile, name: 'Jane', company: nil)

        expect(profile.display_name).to eq('Jane')
      end
    end
  end
end
```

---

## Service Spec Example

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BulkImport::ProfilesService do
  subject(:service) { described_class.new(file:, user:) }

  let(:user) { create(:user, :admin) }

  describe '#call' do
    context 'when the file is valid' do
      let(:file) { fixture_file_upload('spec/fixtures/profiles.csv', 'text/csv') }

      it 'imports all rows' do
        result = service.call

        expect(result.success?).to be(true)
        expect(result.imported_count).to eq(3)
      end

      it 'creates profile records' do
        expect { service.call }.to change(Profile, :count).by(3)
      end

      it 'returns no errors' do
        result = service.call

        expect(result.errors).to be_empty
      end
    end

    context 'when the file has invalid rows' do
      let(:file) { fixture_file_upload('spec/fixtures/profiles_with_errors.csv', 'text/csv') }

      it 'imports valid rows' do
        result = service.call

        expect(result.imported_count).to eq(2)
      end

      it 'collects errors for invalid rows' do
        result = service.call

        expect(result.errors).to include(match(/Row \d+/))
      end
    end

    context 'when the file is nil' do
      let(:file) { nil }

      it 'returns a failure result' do
        result = service.call

        expect(result.success?).to be(false)
        expect(result.errors).to include('File is required')
      end
    end

    context 'with dry_run: true' do
      subject(:service) { described_class.new(file:, user:, dry_run: true) }

      let(:file) { fixture_file_upload('spec/fixtures/profiles.csv', 'text/csv') }

      it 'does not persist records' do
        expect { service.call }.not_to change(Profile, :count)
      end
    end
  end
end
```

---

## Request Spec Example

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'Api::V1::Profiles', type: :request do
  let(:user) { create(:user) }
  let(:headers) { auth_headers_for(user) }

  describe 'GET /api/v1/profiles' do
    context 'when authenticated' do
      let!(:profiles) { create_list(:profile, 3, user:) }

      it 'returns profiles for the current user' do
        get '/api/v1/profiles', headers:

        expect(response).to have_http_status(:ok)
        expect(json_response['profiles'].size).to eq(3)
      end

      it 'includes pagination metadata' do
        get '/api/v1/profiles', headers:

        expect(json_response['meta']).to include(
          'current_page' => 1,
          'total_count' => 3
        )
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get '/api/v1/profiles'

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /api/v1/profiles/:id' do
    let(:profile) { create(:profile, user:) }

    it 'returns the requested profile' do
      get "/api/v1/profiles/#{profile.id}", headers:

      expect(response).to have_http_status(:ok)
      expect(json_response['id']).to eq(profile.id)
    end

    it 'returns not found for missing profile' do
      get '/api/v1/profiles/99999', headers:

      expect(response).to have_http_status(:not_found)
    end
  end

  describe 'POST /api/v1/profiles' do
    let(:valid_params) { { profile: attributes_for(:profile) } }

    it 'creates a new profile' do
      expect {
        post '/api/v1/profiles', params: valid_params, headers:
      }.to change(Profile, :count).by(1)

      expect(response).to have_http_status(:created)
    end

    it 'returns errors for invalid params' do
      post '/api/v1/profiles', params: { profile: { name: '' } }, headers:

      expect(response).to have_http_status(:unprocessable_entity)
      expect(json_response['errors']).to be_present
    end
  end

  describe 'PATCH /api/v1/profiles/:id' do
    let(:profile) { create(:profile, user:) }

    it 'updates the profile' do
      patch "/api/v1/profiles/#{profile.id}",
            params: { profile: { name: 'Updated' } },
            headers:

      expect(response).to have_http_status(:ok)
      expect(profile.reload.name).to eq('Updated')
    end
  end

  describe 'DELETE /api/v1/profiles/:id' do
    let!(:profile) { create(:profile, user:) }

    it 'deletes the profile' do
      expect {
        delete "/api/v1/profiles/#{profile.id}", headers:
      }.to change(Profile, :count).by(-1)

      expect(response).to have_http_status(:no_content)
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
      let(:company) { create(:company) }
      let(:profile) { create(:profile, company:) }

      subject(:result) { described_class.new(profile).call }

      it 'returns a hash with expected keys' do
        expect(result.keys).to include(:id, :name, :email, :company, :created_at)
      end

      it 'includes profile attributes' do
        expect(result).to include(
          id: profile.id,
          name: profile.name,
          email: profile.email
        )
      end

      it 'includes nested company data' do
        expect(result[:company]).to include(
          id: company.id,
          name: company.name
        )
      end

      it 'formats timestamps as ISO 8601' do
        expect(result[:created_at]).to match(/\d{4}-\d{2}-\d{2}T/)
      end
    end

    context 'with a collection' do
      let(:profiles) { create_list(:profile, 3) }

      it 'returns an array of hashes' do
        result = described_class.new(profiles).call

        expect(result).to be_an(Array)
        expect(result.size).to eq(3)
      end
    end

    context 'when company is nil' do
      let(:profile) { create(:profile, company: nil) }

      it 'returns nil for company' do
        result = described_class.new(profile).call

        expect(result[:company]).to be_nil
      end
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
  describe '#perform' do
    let(:import) { create(:import, :pending) }
    let(:service) { instance_double(Sync::AirtableImportService) }
    let(:result) { OpenStruct.new(success?: true, imported_count: 10, error_count: 0) }

    before do
      allow(Sync::AirtableImportService).to receive(:new).and_return(service)
      allow(service).to receive(:call).and_return(result)
    end

    it 'creates and calls the import service' do
      described_class.perform_now(import.id)

      expect(Sync::AirtableImportService).to have_received(:new).with(import:)
      expect(service).to have_received(:call)
    end

    context 'when the import is already completed' do
      let(:import) { create(:import, :completed) }

      it 'skips processing' do
        described_class.perform_now(import.id)

        expect(Sync::AirtableImportService).not_to have_received(:new)
      end
    end

    context 'when the record does not exist' do
      it 'handles gracefully without raising' do
        expect { described_class.perform_now(99999) }.not_to raise_error
      end
    end
  end

  describe 'queue' do
    it 'uses the default queue' do
      expect(described_class.new.queue_name).to eq('default')
    end
  end
end
```
