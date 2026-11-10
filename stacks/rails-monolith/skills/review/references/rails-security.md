# Rails Security Review Checklist

Comprehensive security review checklist for Rails applications. Every code review
must verify these items for any changed files.

---

## 1. SQL Injection Prevention

### What to Check

- No raw SQL with string interpolation
- All user input is parameterized
- `where` clauses use hash syntax or parameterized strings

### Violations

```ruby
# BAD - SQL injection risk
User.where("name = '#{params[:name]}'")
User.where("email LIKE '%#{params[:query]}%'")
ActiveRecord::Base.connection.execute("SELECT * FROM users WHERE id = #{params[:id]}")
```

### Correct Patterns

```ruby
# GOOD - Parameterized queries
User.where(name: params[:name])
User.where('name = ?', params[:name])
User.where('email ILIKE ?', "%#{ActiveRecord::Base.sanitize_sql_like(params[:query])}%")

# GOOD - Using Arel for complex queries
users = User.arel_table
User.where(users[:name].matches("%#{User.sanitize_sql_like(query)}%"))
```

---

## 2. Mass Assignment Protection

### What to Check

- Controllers use strong params (`params.require(:model).permit(...)`)
- No usage of `params.permit!` (permits everything)
- No direct assignment of user-controlled params to models
- Sensitive attributes are never permitted (role, admin, permissions)

### Violations

```ruby
# BAD - Permits all parameters
@user.update(params.permit!)

# BAD - Permits sensitive attributes
params.require(:user).permit(:name, :email, :role, :admin)

# BAD - Direct param assignment
@user.assign_attributes(params[:user])
```

### Correct Patterns

```ruby
# GOOD - Explicit whitelist
def user_params
  params.require(:user).permit(:name, :email, :bio)
end

# GOOD - Separate params for admin actions
def admin_user_params
  params.require(:user).permit(:name, :email, :bio, :role)
end
```

---

## 3. Authentication Checks

### What to Check

- All non-public endpoints require authentication
- `before_action :authenticate_user!` is present (or equivalent)
- Token validation is performed before any data access
- Session/token expiration is configured
- Password reset tokens are single-use and time-limited

### Violations

```ruby
# BAD - No authentication
class ProfilesController < ApplicationController
  def index
    render json: Profile.all
  end
end

# BAD - Skip authentication without justification
class ProfilesController < ApplicationController
  skip_before_action :authenticate_user!

  def show
    render json: Profile.find(params[:id])
  end
end
```

### Correct Patterns

```ruby
# GOOD - Authentication required
class ProfilesController < ApplicationController
  before_action :authenticate_user!

  def index
    render json: current_user.profiles
  end
end

# GOOD - Public endpoints are explicitly marked and limited
class PublicProfilesController < ApplicationController
  skip_before_action :authenticate_user!, only: [:show]

  # Only exposes limited public data
  def show
    profile = Profile.where(public: true).find(params[:id])
    render json: PublicProfilePresenter.new(profile).call
  end
end
```

---

## 4. Authorization Checks

### What to Check

- Users can only access resources they own or are authorized for
- Resource scoping uses `current_user` association, not just ID lookup
- Admin actions have role checks
- Pundit or CanCanCan policies are defined for models

### Violations

```ruby
# BAD - Any authenticated user can access any profile
def show
  @profile = Profile.find(params[:id])
end

# BAD - Any user can update any profile
def update
  @profile = Profile.find(params[:id])
  @profile.update(profile_params)
end
```

### Correct Patterns

```ruby
# GOOD - Scoped to current user
def show
  @profile = current_user.profiles.find(params[:id])
end

# GOOD - Authorization check
def update
  @profile = Profile.find(params[:id])
  authorize @profile  # Pundit
  @profile.update(profile_params)
end

# GOOD - Manual authorization
def destroy
  @profile = Profile.find(params[:id])
  head :forbidden unless @profile.user == current_user
  @profile.destroy!
end
```

---

## 5. CSRF Protection

### What to Check

- `protect_from_forgery` is not disabled globally
- API endpoints use token-based auth (CSRF not applicable for stateless APIs)
- Form-based endpoints include CSRF tokens
- `skip_forgery_protection` is only used for API controllers with token auth

### Violations

```ruby
# BAD - Disabling CSRF globally
class ApplicationController < ActionController::Base
  skip_forgery_protection
end
```

### Correct Patterns

```ruby
# GOOD - CSRF enabled for web, disabled for API with token auth
class ApplicationController < ActionController::Base
  protect_from_forgery with: :exception
end

class Api::BaseController < ActionController::API
  # Token-based auth, CSRF not needed
  before_action :authenticate_user!
end
```

---

## 6. Secrets Management

### What to Check

- No hardcoded API keys, passwords, or tokens in source code
- Secrets are loaded from environment variables or Rails credentials
- `.env` files are in `.gitignore`
- Sensitive data is not logged (filter_parameters configured)
- Database credentials are not in `database.yml` (use ENV vars)

### Violations

```ruby
# BAD - Hardcoded secret
API_KEY = 'sk_live_abc123def456'
HTTParty.get(url, headers: { 'Authorization' => 'Bearer hardcoded_token' })

# BAD - Secret in database.yml
production:
  password: my_database_password
```

### Correct Patterns

```ruby
# GOOD - Environment variable
API_KEY = ENV.fetch('EXTERNAL_API_KEY')

# GOOD - Rails credentials
api_key = Rails.application.credentials.dig(:external_service, :api_key)

# GOOD - Parameter filtering
# config/initializers/filter_parameter_logging.rb
Rails.application.config.filter_parameters += [
  :password, :password_confirmation, :token, :secret,
  :api_key, :access_token, :ssn, :credit_card
]
```

---

## 7. Data Exposure Prevention

### What to Check

- API responses do not leak sensitive fields (password_digest, tokens, internal IDs)
- Presenters explicitly whitelist fields (never serialize entire models)
- Error messages do not reveal internal details (stack traces, SQL queries)
- Logs do not contain PII (emails, names, addresses filtered)

### Violations

```ruby
# BAD - Exposes all attributes
render json: @user

# BAD - Leaks password digest
render json: @user.as_json

# BAD - Detailed error in production
render json: { error: e.message, backtrace: e.backtrace }
```

### Correct Patterns

```ruby
# GOOD - Presenter with explicit fields
render json: UserPresenter.new(@user).call

# GOOD - Generic error in production
render json: { error: 'Internal server error' }, status: :internal_server_error

# GOOD - Structured logging without PII
Rails.logger.info("Profile updated: id=#{profile.id} by user_id=#{current_user.id}")
```

---

## 8. Rate Limiting and Abuse Prevention

### What to Check

- Rate limiting on authentication endpoints (login, password reset)
- Rate limiting on expensive operations (search, bulk imports)
- Account lockout after failed login attempts
- Pagination on all list endpoints (no unbounded queries)

### Correct Patterns

```ruby
# Rack::Attack configuration
# config/initializers/rack_attack.rb
Rack::Attack.throttle('login_attempts', limit: 5, period: 60) do |req|
  req.ip if req.path == '/api/v1/auth/login' && req.post?
end

# Controller pagination
def index
  profiles = Profile.page(params[:page]).per([params[:per_page].to_i, 100].min)
  render json: profiles
end
```
