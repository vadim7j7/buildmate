# Rails Security Patterns

Security patterns and best practices for Ruby on Rails applications. All agents
must follow these patterns to prevent OWASP Top 10 vulnerabilities.

---

## 1. SQL Injection Prevention

**Always** use parameterized queries. Never interpolate user input into SQL.

```ruby
# CORRECT - parameterized query
User.where(email: params[:email])
User.where("email = ?", params[:email])
User.where("email = :email", email: params[:email])

# CORRECT - find methods are safe
User.find(params[:id])
User.find_by(id: params[:id])

# WRONG - SQL injection vulnerability
User.where("email = '#{params[:email]}'")
User.where("email = " + params[:email])
User.find_by_sql("SELECT * FROM users WHERE email = '#{params[:email]}'")

# WRONG - order/pluck with user input
User.order(params[:sort])  # Vulnerable!
User.pluck(params[:column])  # Vulnerable!

# CORRECT - whitelist for dynamic columns
ALLOWED_SORT_COLUMNS = %w[created_at updated_at name].freeze

def safe_order(column)
  return :created_at unless ALLOWED_SORT_COLUMNS.include?(column)
  column.to_sym
end

User.order(safe_order(params[:sort]))
```

### Arel for Complex Queries

```ruby
# CORRECT - Arel is safe for complex queries
users = User.arel_table
User.where(users[:email].matches("%#{User.sanitize_sql_like(params[:q])}%"))

# CORRECT - sanitize LIKE patterns
User.where("name LIKE ?", "%#{User.sanitize_sql_like(params[:q])}%")
```

---

## 2. Mass Assignment Protection

Use strong parameters. Never permit all attributes.

```ruby
# CORRECT - explicit permit list
def user_params
  params.require(:user).permit(:name, :email, :avatar)
end

# CORRECT - nested attributes
def order_params
  params.require(:order).permit(
    :status,
    line_items_attributes: [:id, :product_id, :quantity, :_destroy]
  )
end

# WRONG - permit all
params.require(:user).permit!

# WRONG - permitting sensitive fields
params.require(:user).permit(:name, :email, :admin, :role)
```

### Attribute Protection in Models

```ruby
class User < ApplicationRecord
  # Attributes that should never be mass-assigned
  attr_readonly :uuid, :created_at

  # Use enum with prefix to avoid method conflicts
  enum :role, { member: 0, admin: 1, superadmin: 2 }, prefix: true
end
```

---

## 3. Authentication Security

### Password Handling

```ruby
class User < ApplicationRecord
  has_secure_password

  # Minimum password requirements
  validates :password, length: { minimum: 12 }, if: :password_required?
  validates :password, format: {
    with: /\A(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
    message: "must include uppercase, lowercase, and number"
  }, if: :password_required?

  private

  def password_required?
    new_record? || password.present?
  end
end
```

### Session Security

```ruby
# config/initializers/session_store.rb
Rails.application.config.session_store :cookie_store,
  key: '_myapp_session',
  secure: Rails.env.production?,
  httponly: true,
  same_site: :lax,
  expire_after: 24.hours

# Regenerate session after login (prevent session fixation)
class SessionsController < ApplicationController
  def create
    user = User.authenticate(params[:email], params[:password])
    if user
      reset_session  # Regenerate session ID
      session[:user_id] = user.id
      redirect_to dashboard_path
    else
      flash.now[:error] = "Invalid credentials"
      render :new
    end
  end

  def destroy
    reset_session  # Clear all session data
    redirect_to root_path
  end
end
```

### Token Security

```ruby
class User < ApplicationRecord
  has_secure_token :api_token
  has_secure_token :password_reset_token

  def regenerate_api_token!
    regenerate_api_token
    update!(api_token_created_at: Time.current)
  end

  def api_token_expired?
    api_token_created_at < 30.days.ago
  end
end

# CORRECT - constant-time comparison for tokens
def authenticate_token(provided_token)
  ActiveSupport::SecurityUtils.secure_compare(
    api_token,
    provided_token.to_s
  )
end

# WRONG - regular comparison (timing attack vulnerable)
def authenticate_token(provided_token)
  api_token == provided_token
end
```

---

## 4. Authorization Patterns

### Pundit Policies

```ruby
# app/policies/project_policy.rb
class ProjectPolicy < ApplicationPolicy
  def show?
    record.public? || record.team.members.include?(user)
  end

  def update?
    record.team.admins.include?(user)
  end

  def destroy?
    record.team.owner == user
  end

  class Scope < Scope
    def resolve
      if user.admin?
        scope.all
      else
        scope.joins(:team).where(teams: { id: user.team_ids })
      end
    end
  end
end

# Controller usage
class ProjectsController < ApplicationController
  def show
    @project = Project.find(params[:id])
    authorize @project  # Raises Pundit::NotAuthorizedError if unauthorized
  end

  def index
    @projects = policy_scope(Project)
  end
end
```

### Secure Direct Object References

```ruby
# WRONG - IDOR vulnerability
def show
  @document = Document.find(params[:id])
end

# CORRECT - scope to current user
def show
  @document = current_user.documents.find(params[:id])
end

# CORRECT - use authorization
def show
  @document = Document.find(params[:id])
  authorize @document
end
```

---

## 5. XSS Prevention

Rails escapes HTML by default. Be careful with `html_safe` and `raw`.

```erb
<%# CORRECT - auto-escaped %>
<p><%= @user.bio %></p>

<%# CORRECT - explicit sanitization for user HTML %>
<div><%= sanitize @post.content, tags: %w[p br strong em a], attributes: %w[href] %></div>

<%# WRONG - bypasses escaping %>
<p><%= @user.bio.html_safe %></p>
<p><%= raw @user.bio %></p>

<%# WRONG - unescaped in JavaScript %>
<script>
  var name = "<%= @user.name %>";  // XSS if name contains quotes
</script>

<%# CORRECT - JSON encoding for JavaScript %>
<script>
  var name = <%= @user.name.to_json %>;
  var data = <%= @user.as_json.to_json %>;
</script>
```

### Content Security Policy

```ruby
# config/initializers/content_security_policy.rb
Rails.application.configure do
  config.content_security_policy do |policy|
    policy.default_src :self
    policy.font_src    :self, :data
    policy.img_src     :self, :data, "https:"
    policy.object_src  :none
    policy.script_src  :self
    policy.style_src   :self, :unsafe_inline
    policy.connect_src :self

    # Report violations
    policy.report_uri "/csp-reports"
  end

  config.content_security_policy_nonce_generator = ->(request) {
    SecureRandom.base64(16)
  }
end
```

---

## 6. CSRF Protection

Rails includes CSRF protection by default. Keep it enabled.

```ruby
class ApplicationController < ActionController::Base
  protect_from_forgery with: :exception

  # For API endpoints that use token auth instead of sessions
  skip_before_action :verify_authenticity_token, if: :api_request?

  private

  def api_request?
    request.format.json? && request.headers["Authorization"].present?
  end
end
```

### AJAX Requests

```javascript
// Rails includes CSRF token in meta tags
// Include in AJAX requests:
const token = document.querySelector('meta[name="csrf-token"]').content;

fetch('/api/resource', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
});
```

---

## 7. File Upload Security

```ruby
class Document < ApplicationRecord
  has_one_attached :file

  # Validate content type
  validates :file, content_type: {
    in: %w[application/pdf image/png image/jpeg],
    message: "must be a PDF, PNG, or JPEG"
  }

  # Validate file size
  validates :file, size: { less_than: 10.megabytes }
end

# Using ActiveStorage validations gem
# Gemfile: gem 'active_storage_validations'

class Avatar < ApplicationRecord
  has_one_attached :image

  validates :image,
    content_type: ['image/png', 'image/jpeg', 'image/webp'],
    size: { less_than: 5.megabytes },
    dimension: { width: { max: 4000 }, height: { max: 4000 } }
end
```

### Secure File Serving

```ruby
# Serve files through controller for access control
class DocumentsController < ApplicationController
  def download
    @document = current_user.documents.find(params[:id])
    redirect_to rails_blob_url(@document.file, disposition: "attachment")
  end
end

# Configure private storage
# config/storage.yml
private:
  service: S3
  access_key_id: <%= Rails.application.credentials.dig(:aws, :access_key_id) %>
  secret_access_key: <%= Rails.application.credentials.dig(:aws, :secret_access_key) %>
  region: us-east-1
  bucket: myapp-private
  private: true
```

---

## 8. Sensitive Data Protection

### Credentials Management

```ruby
# Store secrets in credentials, never in code
# Edit: rails credentials:edit

# Access credentials
Rails.application.credentials.secret_key_base
Rails.application.credentials.dig(:aws, :access_key_id)
Rails.application.credentials.stripe[:secret_key]

# Environment-specific credentials
# rails credentials:edit --environment production
Rails.application.credentials.database_url  # Uses RAILS_ENV
```

### Logging Sanitization

```ruby
# config/initializers/filter_parameter_logging.rb
Rails.application.config.filter_parameters += [
  :password,
  :password_confirmation,
  :token,
  :api_key,
  :secret,
  :credit_card,
  :ssn,
  /authorization/i,
  /bearer/i
]

# Filter in ActiveRecord logs
# config/application.rb
config.filter_parameters += [:encrypted_password, :reset_password_token]
```

### Encryption at Rest

```ruby
class User < ApplicationRecord
  # Rails 7+ ActiveRecord Encryption
  encrypts :ssn, deterministic: true  # Allows querying
  encrypts :medical_notes  # Non-deterministic, more secure
end

# config/credentials.yml.enc
active_record_encryption:
  primary_key: <32-byte key>
  deterministic_key: <32-byte key>
  key_derivation_salt: <salt>
```

---

## 9. Rate Limiting

```ruby
# Using Rack::Attack
# config/initializers/rack_attack.rb
class Rack::Attack
  # Throttle login attempts
  throttle("logins/ip", limit: 5, period: 60.seconds) do |req|
    req.ip if req.path == "/login" && req.post?
  end

  # Throttle API requests
  throttle("api/ip", limit: 100, period: 1.minute) do |req|
    req.ip if req.path.start_with?("/api/")
  end

  # Throttle by user for authenticated requests
  throttle("api/user", limit: 1000, period: 1.hour) do |req|
    if req.path.start_with?("/api/") && req.env["warden"].user
      req.env["warden"].user.id
    end
  end

  # Block suspicious requests
  blocklist("block bad IPs") do |req|
    Rack::Attack::Fail2Ban.filter("suspicious-#{req.ip}", maxretry: 3, findtime: 1.hour, bantime: 1.day) do
      req.path.include?("wp-admin") || req.path.include?(".php")
    end
  end
end
```

---

## 10. Security Headers

```ruby
# config/application.rb or initializer
config.action_dispatch.default_headers = {
  'X-Frame-Options' => 'SAMEORIGIN',
  'X-XSS-Protection' => '0',  # Disabled, use CSP instead
  'X-Content-Type-Options' => 'nosniff',
  'X-Download-Options' => 'noopen',
  'X-Permitted-Cross-Domain-Policies' => 'none',
  'Referrer-Policy' => 'strict-origin-when-cross-origin',
  'Permissions-Policy' => 'geolocation=(), microphone=(), camera=()'
}

# Force HTTPS in production
# config/environments/production.rb
config.force_ssl = true
config.ssl_options = { hsts: { subdomains: true, preload: true, expires: 1.year } }
```

---

## Security Checklist

Before deploying any feature, verify:

- [ ] No SQL injection (parameterized queries only)
- [ ] Strong parameters defined (no `permit!`)
- [ ] Authorization checks on all actions
- [ ] No `html_safe` or `raw` with user input
- [ ] CSRF protection enabled
- [ ] File uploads validated (type, size)
- [ ] Sensitive data filtered from logs
- [ ] Secrets in credentials, not code
- [ ] Rate limiting on sensitive endpoints
- [ ] Security headers configured
