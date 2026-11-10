# Sinatra Authentication Patterns

Pick one mechanism per client type:

| Client | Mechanism |
|--------|-----------|
| Browser on the same site (server-rendered or same-origin SPA) | Cookie session (`enable :sessions`) + CSRF token |
| Mobile app, CLI, third-party client | Bearer token: JWT, or an opaque token stored in the DB |

Passwords are always hashed with `bcrypt`; secrets come from `ENV`, never the repo.

---

## 1. Password Hashing (Sequel model)

```ruby
# frozen_string_literal: true

# Gemfile: gem "bcrypt"
require "bcrypt"

class User < Sequel::Model
  def password=(plain)
    self.password_digest = BCrypt::Password.create(plain)
  end

  def authenticate(plain)
    BCrypt::Password.new(password_digest) == plain && self
  end

  def self.authenticate_by(email:, password:)
    user = first(email: email.to_s.strip.downcase)
    return user&.authenticate(password) if user

    BCrypt::Password.create(password.to_s) # spend the same time when the email is unknown
    nil
  end
end
```

---

## 2. Cookie Sessions

Sinatra 4 sessions use the `rack-session` gem (a Sinatra dependency).

```ruby
# frozen_string_literal: true

class App < Sinatra::Base
  configure do
    enable :sessions
    set :session_secret, ENV.fetch("SESSION_SECRET") # 64+ random bytes: `ruby -rsecurerandom -e 'puts SecureRandom.hex(64)'`
    set :sessions, httponly: true, same_site: :lax, secure: production?, expire_after: 14 * 24 * 3600
  end

  # CSRF for form/cookie clients (not enabled by Sinatra's default protection)
  use Rack::Protection::AuthenticityToken

  post "/session" do
    user = User.authenticate_by(email: params[:email], password: params[:password])
    halt 401, json(error: { code: "invalid_credentials", message: "Invalid email or password" }) unless user

    session.clear                 # new session id on sign-in (prevents fixation)
    session[:user_id] = user.id
    json user: { id: user.id, email: user.email }
  end

  delete "/session" do
    session.clear
    status 204
  end
end
```

Forms and fetch calls send the token from `Rack::Protection::AuthenticityToken.token(session)`
as `authenticity_token` (form field) or the `X-CSRF-Token` header.

---

## 3. JWT Bearer Tokens

```ruby
# frozen_string_literal: true

# Gemfile: gem "jwt"
module Auth
  module Tokens
    ALGORITHM = "HS256"
    TTL = 15 * 60 # short-lived access tokens; refresh with a DB-backed token if needed

    def self.issue(user_id)
      now = Time.now.to_i
      JWT.encode({ sub: user_id, iat: now, exp: now + TTL }, secret, ALGORITHM)
    end

    def self.decode(token)
      payload, = JWT.decode(token, secret, true, algorithm: ALGORITHM) # pin the algorithm
      payload
    rescue JWT::DecodeError # includes ExpiredSignature and VerificationError
      nil
    end

    def self.secret = ENV.fetch("JWT_SECRET")
  end
end
```

Prefer an opaque random token stored in the DB (`SecureRandom.urlsafe_base64(32)`,
store its SHA-256) when you need instant revocation (sign-out, stolen device):
a JWT stays valid until `exp`.

---

## 4. Helpers Used by Routes

```ruby
# frozen_string_literal: true

module Helpers
  module Authentication
    def current_user
      return @current_user if defined?(@current_user)

      @current_user = user_from_token || user_from_session
    end

    def authenticate!
      raise Errors::AuthorizationError, "Sign in required" unless current_user
    end

    private

    def user_from_token
      header = request.env["HTTP_AUTHORIZATION"].to_s
      return unless header.start_with?("Bearer ")

      payload = Auth::Tokens.decode(header.delete_prefix("Bearer "))
      payload && User.with_pk(payload["sub"])
    end

    def user_from_session
      session[:user_id] && User.with_pk(session[:user_id])
    end
  end
end
```

```ruby
app.get "/projects" do
  authenticate!
  json ProjectService.new(user: current_user).list.map(&:to_h)
end
```

Scope every query through `current_user` (`current_user.projects_dataset`) so a
user can never load another user's record by guessing an id.

---

## 5. rack-protection and Hardening

- Sinatra enables `rack-protection` by default (path traversal, JSON CSRF, IP
  spoofing, session hijacking, frame options). Don't `disable :protection`;
  turn off a single module only with a reason:
  `set :protection, except: [:json_csrf]`.
- Add `Rack::Protection::AuthenticityToken` when cookies authenticate
  state-changing requests (section 2). Pure bearer-token APIs don't need it.
- Throttle sign-in: `rack-attack` works with any Rack app
  (`use Rack::Attack` + `throttle("logins/ip", limit: 5, period: 60) { |r| r.ip if r.post? && r.path == "/session" }`).
- CORS for browser clients on another origin: `rack-cors` with an explicit
  origin list, never `*` together with credentials.
- Never log passwords, tokens or the `Authorization` header.

---

## 6. Testing

```ruby
def auth_header(user)
  { "HTTP_AUTHORIZATION" => "Bearer #{Auth::Tokens.issue(user.id)}" }
end

it "rejects requests without a token" do
  get "/projects"
  expect(last_response.status).to eq(401)
end

it "lists the user's projects" do
  get "/projects", {}, auth_header(user)
  expect(last_response.status).to eq(200)
end

it "rejects an expired token" do
  token = Auth::Tokens.issue(user.id)
  Timecop.travel(Time.now + 16 * 60) do   # or travel_to with ActiveSupport
    get "/projects", {}, "HTTP_AUTHORIZATION" => "Bearer #{token}"
  end
  expect(last_response.status).to eq(401)
end
```
