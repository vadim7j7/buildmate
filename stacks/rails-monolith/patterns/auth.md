# Rails Authentication Patterns

Authentication patterns using Devise and related gems.

---

## 1. Devise Setup

### Gemfile

```ruby
gem 'devise'
gem 'devise-jwt'  # For API authentication
```

### User Model

```ruby
# frozen_string_literal: true

class User < ApplicationRecord
  devise :database_authenticatable, :registerable,
         :recoverable, :rememberable, :validatable,
         :confirmable, :lockable, :trackable,
         :jwt_authenticatable, jwt_revocation_strategy: JwtDenylist

  has_many :sessions, dependent: :destroy

  validates :email, presence: true, uniqueness: { case_sensitive: false }
  validates :name, presence: true, length: { minimum: 2, maximum: 100 }

  def jwt_payload
    { 'sub' => id, 'email' => email }
  end
end
```

### JWT Denylist

```ruby
# frozen_string_literal: true

class JwtDenylist < ApplicationRecord
  include Devise::JWT::RevocationStrategies::Denylist

  self.table_name = 'jwt_denylists'
end
```

---

## 2. API Authentication Controller

```ruby
# frozen_string_literal: true

module Api
  module V1
    class SessionsController < Devise::SessionsController
      respond_to :json

      private

      def respond_with(resource, _opts = {})
        render json: UserSerializer.new(resource).serialize, status: :ok
      end

      def respond_to_on_destroy
        if current_user
          render json: { message: 'Logged out successfully' }, status: :ok
        else
          render json: { error: 'Not logged in' }, status: :unauthorized
        end
      end
    end
  end
end
```

### Registrations Controller

```ruby
# frozen_string_literal: true

module Api
  module V1
    class RegistrationsController < Devise::RegistrationsController
      respond_to :json

      private

      def respond_with(resource, _opts = {})
        if resource.persisted?
          render json: UserSerializer.new(resource).serialize, status: :created
        else
          render json: { errors: resource.errors.full_messages }, status: :unprocessable_entity
        end
      end
    end
  end
end
```

---

## 3. Current User Helper

```ruby
# frozen_string_literal: true

module Api
  class ApplicationController < ActionController::API
    before_action :authenticate_user!

    private

    def current_user
      @current_user ||= warden.authenticate(scope: :user)
    end

    def authenticate_user!
      return if current_user

      render json: { error: 'Unauthorized' }, status: :unauthorized
    end

    def authorize_admin!
      return if current_user&.admin?

      render json: { error: 'Forbidden' }, status: :forbidden
    end
  end
end
```

---

## 4. Token-Based Authentication (Without Devise)

### Session Model

```ruby
# frozen_string_literal: true

class Session < ApplicationRecord
  belongs_to :user

  before_create :generate_token
  before_create :set_expiry

  scope :active, -> { where('expires_at > ?', Time.current) }
  scope :expired, -> { where('expires_at <= ?', Time.current) }

  def expired?
    expires_at <= Time.current
  end

  def refresh!
    update!(expires_at: 7.days.from_now)
  end

  private

  def generate_token
    self.token = SecureRandom.urlsafe_base64(32)
  end

  def set_expiry
    self.expires_at = 7.days.from_now
  end
end
```

### Auth Service

```ruby
# frozen_string_literal: true

module Auth
  class AuthenticateService < ApplicationService
    def initialize(email:, password:)
      @email = email
      @password = password
    end

    def call
      user = User.find_by(email: @email.downcase)

      return failure(:invalid_credentials) unless user&.authenticate(@password)
      return failure(:account_locked) if user.locked?
      return failure(:email_not_confirmed) unless user.confirmed?

      session = user.sessions.create!
      success(user: user, token: session.token)
    end
  end
end
```

---

## 5. Password Reset Flow

### Request Reset

```ruby
# frozen_string_literal: true

module Auth
  class RequestPasswordResetService < ApplicationService
    def initialize(email:)
      @email = email
    end

    def call
      user = User.find_by(email: @email.downcase)

      # Always return success to prevent email enumeration
      return success unless user

      token = user.generate_password_reset_token!
      UserMailer.password_reset(user).deliver_later

      success
    end
  end
end
```

### Reset Password

```ruby
# frozen_string_literal: true

module Auth
  class ResetPasswordService < ApplicationService
    def initialize(token:, password:, password_confirmation:)
      @token = token
      @password = password
      @password_confirmation = password_confirmation
    end

    def call
      user = User.find_by_password_reset_token(@token)

      return failure(:invalid_token) unless user
      return failure(:token_expired) if user.password_reset_expired?

      if user.update(password: @password, password_confirmation: @password_confirmation)
        user.clear_password_reset_token!
        success(user: user)
      else
        failure(:validation_failed, errors: user.errors.full_messages)
      end
    end
  end
end
```

---

## 6. Email Confirmation

### Confirmation Token

```ruby
# frozen_string_literal: true

class User < ApplicationRecord
  def generate_confirmation_token!
    update!(
      confirmation_token: SecureRandom.urlsafe_base64(32),
      confirmation_sent_at: Time.current
    )
    confirmation_token
  end

  def confirm!
    update!(
      confirmed_at: Time.current,
      confirmation_token: nil
    )
  end

  def confirmed?
    confirmed_at.present?
  end

  def confirmation_period_valid?
    confirmation_sent_at && confirmation_sent_at > 24.hours.ago
  end
end
```

---

## 7. OAuth Integration (OmniAuth)

### Gemfile

```ruby
gem 'omniauth'
gem 'omniauth-google-oauth2'
gem 'omniauth-github'
gem 'omniauth-rails_csrf_protection'
```

### User Model with OAuth

```ruby
# frozen_string_literal: true

class User < ApplicationRecord
  has_many :identities, dependent: :destroy

  def self.from_omniauth(auth)
    identity = Identity.find_or_create_by(provider: auth.provider, uid: auth.uid)

    if identity.user
      identity.user
    else
      user = find_or_create_by(email: auth.info.email) do |u|
        u.name = auth.info.name
        u.password = SecureRandom.hex(16)
        u.skip_confirmation! if u.respond_to?(:skip_confirmation!)
      end
      identity.update!(user: user)
      user
    end
  end
end

class Identity < ApplicationRecord
  belongs_to :user

  validates :provider, :uid, presence: true
  validates :uid, uniqueness: { scope: :provider }
end
```

---

## 8. Rate Limiting

```ruby
# frozen_string_literal: true

class Rack::Attack
  # Limit login attempts
  throttle('logins/ip', limit: 5, period: 60.seconds) do |req|
    req.ip if req.path == '/api/v1/sessions' && req.post?
  end

  # Limit password reset requests
  throttle('password_resets/ip', limit: 5, period: 1.hour) do |req|
    req.ip if req.path == '/api/v1/passwords' && req.post?
  end

  # Limit API requests per user
  throttle('api/user', limit: 1000, period: 1.hour) do |req|
    req.env['warden']&.user&.id if req.path.start_with?('/api/')
  end
end
```

---

## 9. Security Best Practices

### Password Requirements

```ruby
# frozen_string_literal: true

class User < ApplicationRecord
  validate :password_complexity

  private

  def password_complexity
    return unless password.present?

    unless password.match?(/\A(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}\z/)
      errors.add(:password, 'must include at least one lowercase letter, one uppercase letter, and one digit')
    end
  end
end
```

### Secure Headers

```ruby
# config/initializers/secure_headers.rb
SecureHeaders::Configuration.default do |config|
  config.hsts = "max-age=#{1.year.to_i}; includeSubdomains"
  config.x_frame_options = "DENY"
  config.x_content_type_options = "nosniff"
  config.x_xss_protection = "1; mode=block"
  config.referrer_policy = %w[strict-origin-when-cross-origin]
end
```

---

## 10. Testing Authentication

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'Sessions', type: :request do
  describe 'POST /api/v1/sessions' do
    let(:user) { create(:user, password: 'Password123!') }

    context 'with valid credentials' do
      it 'returns user and token' do
        post '/api/v1/sessions', params: {
          user: { email: user.email, password: 'Password123!' }
        }

        expect(response).to have_http_status(:ok)
        expect(response.headers['Authorization']).to be_present
      end
    end

    context 'with invalid credentials' do
      it 'returns unauthorized' do
        post '/api/v1/sessions', params: {
          user: { email: user.email, password: 'wrong' }
        }

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
```
