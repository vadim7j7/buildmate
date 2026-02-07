# Rails OAuth Patterns

OAuth integration patterns using OmniAuth.

---

## 1. OmniAuth Setup

### Gemfile

```ruby
gem 'omniauth'
gem 'omniauth-google-oauth2'
gem 'omniauth-github'
gem 'omniauth-facebook'
gem 'omniauth-rails_csrf_protection'
```

### Initializer

```ruby
# config/initializers/omniauth.rb
Rails.application.config.middleware.use OmniAuth::Builder do
  provider :google_oauth2,
           ENV['GOOGLE_CLIENT_ID'],
           ENV['GOOGLE_CLIENT_SECRET'],
           scope: 'email,profile',
           prompt: 'select_account'

  provider :github,
           ENV['GITHUB_CLIENT_ID'],
           ENV['GITHUB_CLIENT_SECRET'],
           scope: 'user:email'

  provider :facebook,
           ENV['FACEBOOK_APP_ID'],
           ENV['FACEBOOK_APP_SECRET'],
           scope: 'email,public_profile'
end

OmniAuth.config.allowed_request_methods = [:post]
OmniAuth.config.silence_get_warning = true
```

---

## 2. Identity Model

```ruby
# frozen_string_literal: true

# Stores OAuth provider identities linked to users.
#
class Identity < ApplicationRecord
  belongs_to :user

  validates :provider, :uid, presence: true
  validates :uid, uniqueness: { scope: :provider }

  encrypts :access_token
  encrypts :refresh_token

  scope :for_provider, ->(provider) { where(provider: provider) }

  def expired?
    expires_at.present? && expires_at < Time.current
  end

  def refresh_if_needed!
    return unless expired?
    return unless refresh_token.present?

    refresher = "OAuth::#{provider.camelize}Refresher".constantize.new(self)
    refresher.call
  end
end
```

### Migration

```ruby
class CreateIdentities < ActiveRecord::Migration[7.1]
  def change
    create_table :identities, id: :uuid do |t|
      t.references :user, null: false, foreign_key: true, type: :uuid
      t.string :provider, null: false
      t.string :uid, null: false
      t.text :access_token
      t.text :refresh_token
      t.datetime :expires_at
      t.jsonb :raw_info, default: {}

      t.timestamps
    end

    add_index :identities, [:provider, :uid], unique: true
  end
end
```

---

## 3. OAuth Callback Controller

```ruby
# frozen_string_literal: true

module Users
  class OmniauthCallbacksController < ApplicationController
    skip_before_action :authenticate_user!
    skip_before_action :verify_authenticity_token, only: [:create]

    def create
      result = OAuth::HandleCallbackService.call(
        auth: request.env['omniauth.auth'],
        current_user: current_user
      )

      if result.success?
        sign_in(result.user)
        redirect_to after_sign_in_path, notice: 'Successfully signed in!'
      else
        redirect_to login_path, alert: result.error
      end
    end

    def failure
      redirect_to login_path, alert: 'Authentication failed. Please try again.'
    end

    private

    def after_sign_in_path
      stored_location_for(:user) || root_path
    end
  end
end
```

---

## 4. OAuth Callback Service

```ruby
# frozen_string_literal: true

module OAuth
  class HandleCallbackService < ApplicationService
    def initialize(auth:, current_user: nil)
      @auth = auth
      @current_user = current_user
    end

    def call
      identity = find_or_create_identity

      if identity.user
        update_identity(identity)
        success(user: identity.user)
      elsif @current_user
        link_identity_to_user(identity, @current_user)
        success(user: @current_user)
      else
        user = find_or_create_user
        link_identity_to_user(identity, user)
        success(user: user)
      end
    rescue ActiveRecord::RecordInvalid => e
      failure(:validation_failed, errors: e.record.errors.full_messages)
    end

    private

    attr_reader :auth, :current_user

    def find_or_create_identity
      Identity.find_or_initialize_by(
        provider: auth.provider,
        uid: auth.uid
      )
    end

    def update_identity(identity)
      identity.update!(
        access_token: auth.credentials&.token,
        refresh_token: auth.credentials&.refresh_token,
        expires_at: auth.credentials&.expires_at&.then { |t| Time.at(t) },
        raw_info: auth.extra&.raw_info&.to_h
      )
    end

    def link_identity_to_user(identity, user)
      identity.user = user
      update_identity(identity)
    end

    def find_or_create_user
      User.find_or_create_by!(email: auth.info.email) do |user|
        user.name = auth.info.name
        user.password = SecureRandom.hex(16)
        user.skip_confirmation! if user.respond_to?(:skip_confirmation!)
      end
    end
  end
end
```

---

## 5. Token Refresh Service

```ruby
# frozen_string_literal: true

module OAuth
  class GoogleRefresher < ApplicationService
    REFRESH_URL = 'https://oauth2.googleapis.com/token'

    def initialize(identity)
      @identity = identity
    end

    def call
      response = HTTP.post(REFRESH_URL, form: {
        client_id: ENV['GOOGLE_CLIENT_ID'],
        client_secret: ENV['GOOGLE_CLIENT_SECRET'],
        refresh_token: identity.refresh_token,
        grant_type: 'refresh_token'
      })

      if response.status.success?
        data = JSON.parse(response.body)
        identity.update!(
          access_token: data['access_token'],
          expires_at: Time.current + data['expires_in'].seconds
        )
        success
      else
        failure(:refresh_failed)
      end
    end

    private

    attr_reader :identity
  end
end
```

---

## 6. Routes Configuration

```ruby
# config/routes.rb
Rails.application.routes.draw do
  # OmniAuth callbacks
  get '/auth/:provider/callback', to: 'users/omniauth_callbacks#create'
  get '/auth/failure', to: 'users/omniauth_callbacks#failure'

  # API OAuth endpoints
  namespace :api do
    namespace :v1 do
      post '/auth/:provider/callback', to: 'oauth#callback'
      delete '/auth/:provider', to: 'oauth#destroy'
    end
  end
end
```

---

## 7. API OAuth Controller

```ruby
# frozen_string_literal: true

module Api
  module V1
    class OauthController < ApplicationController
      def callback
        result = OAuth::HandleApiCallbackService.call(
          provider: params[:provider],
          code: params[:code],
          redirect_uri: params[:redirect_uri]
        )

        if result.success?
          render json: {
            user: UserSerializer.new(result.user).serialize,
            token: result.token
          }
        else
          render json: { error: result.error }, status: :unauthorized
        end
      end

      def destroy
        identity = current_user.identities.for_provider(params[:provider]).first

        if identity&.destroy
          render json: { message: 'Provider unlinked' }
        else
          render json: { error: 'Provider not found' }, status: :not_found
        end
      end
    end
  end
end
```

---

## 8. Testing OAuth

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe OAuth::HandleCallbackService do
  let(:auth_hash) do
    OmniAuth::AuthHash.new(
      provider: 'google_oauth2',
      uid: '123456',
      info: {
        email: 'user@example.com',
        name: 'Test User'
      },
      credentials: {
        token: 'access_token',
        refresh_token: 'refresh_token',
        expires_at: 1.hour.from_now.to_i
      }
    )
  end

  describe '#call' do
    context 'with new user' do
      it 'creates user and identity' do
        result = described_class.call(auth: auth_hash)

        expect(result).to be_success
        expect(result.user.email).to eq('user@example.com')
        expect(result.user.identities.count).to eq(1)
      end
    end

    context 'with existing identity' do
      let!(:user) { create(:user, email: 'user@example.com') }
      let!(:identity) do
        create(:identity, user: user, provider: 'google_oauth2', uid: '123456')
      end

      it 'returns existing user' do
        result = described_class.call(auth: auth_hash)

        expect(result).to be_success
        expect(result.user).to eq(user)
      end

      it 'updates identity tokens' do
        result = described_class.call(auth: auth_hash)

        identity.reload
        expect(identity.access_token).to eq('access_token')
      end
    end

    context 'when linking to current user' do
      let(:current_user) { create(:user) }

      it 'links identity to current user' do
        result = described_class.call(auth: auth_hash, current_user: current_user)

        expect(result).to be_success
        expect(current_user.identities.count).to eq(1)
      end
    end
  end
end
```

---

## 9. Mock OAuth for Tests

```ruby
# spec/support/omniauth.rb
OmniAuth.config.test_mode = true

def mock_google_auth(email: 'user@example.com', uid: '123456')
  OmniAuth.config.mock_auth[:google_oauth2] = OmniAuth::AuthHash.new(
    provider: 'google_oauth2',
    uid: uid,
    info: { email: email, name: 'Test User' },
    credentials: { token: 'token', refresh_token: 'refresh', expires_at: 1.hour.from_now.to_i }
  )
end

def mock_oauth_failure(provider)
  OmniAuth.config.mock_auth[provider] = :invalid_credentials
end

RSpec.configure do |config|
  config.before(:each) do
    OmniAuth.config.mock_auth[:google_oauth2] = nil
    OmniAuth.config.mock_auth[:github] = nil
  end
end
```
