# Rails Verification Pattern

## Overview

Rails implementations are verified by making actual HTTP requests to the dev server
and validating responses, status codes, and error handling.

## Prerequisites

- Rails server running on port 3000 (or configured port)
- Test database seeded
- Authentication tokens available for protected endpoints

## Verification Workflow

### 1. Start Dev Server

```bash
# Check if running
curl -s http://localhost:3000/health || bundle exec rails server -d

# Wait for ready
until curl -s http://localhost:3000/health; do sleep 1; done
```

### 2. Test Endpoint

```bash
# Example: POST /api/users
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"user": {"email": "test@example.com", "name": "Test"}}' \
  -w "\n%{http_code}"
```

### 3. Validate Response

| Check | Expected |
|-------|----------|
| Status code | 201 for create, 200 for success |
| Content-Type | application/json |
| Body structure | Matches serializer output |
| Timestamps | present and valid |

### 4. Test Error Cases

```bash
# Missing required field
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"user": {"name": "Test"}}' \
  -w "\n%{http_code}"
# Expected: 422 Unprocessable Entity

# Invalid data
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"user": {"email": "invalid"}}' \
  -w "\n%{http_code}"
# Expected: 422 Unprocessable Entity

# Not found
curl http://localhost:3000/api/users/99999 -w "\n%{http_code}"
# Expected: 404 Not Found

# Unauthorized
curl http://localhost:3000/api/admin/users -w "\n%{http_code}"
# Expected: 401 Unauthorized
```

## Common Validations

### Model Validations

```ruby
# Test in rails console or via API
user = User.new(email: "invalid")
user.valid? # => false
user.errors.full_messages # => ["Email is invalid"]
```

### Association Loading

```bash
# Verify includes work
curl http://localhost:3000/api/posts?include=author,comments \
  | jq '.data[0].author, .data[0].comments'
```

### Pagination

```bash
# Verify pagination
curl "http://localhost:3000/api/posts?page=1&per_page=10" \
  | jq '.meta.total, .meta.page, .meta.per_page'
```

## Auto-Fix Patterns

### Missing Route

**Error:** `No route matches [POST] "/api/users"`

**Fix:**
```ruby
# config/routes.rb
namespace :api do
  resources :users, only: [:create]
end
```

### Missing Action

**Error:** `The action 'create' could not be found`

**Fix:**
```ruby
# app/controllers/api/users_controller.rb
def create
  @user = User.new(user_params)
  if @user.save
    render json: @user, status: :created
  else
    render json: { errors: @user.errors }, status: :unprocessable_entity
  end
end
```

### Strong Parameters Missing

**Error:** `param is missing or the value is empty: user`

**Fix:**
```ruby
private

def user_params
  params.require(:user).permit(:email, :name)
end
```

### Validation Error

**Error:** Response has no error details

**Fix:**
```ruby
render json: {
  errors: @user.errors.full_messages,
  details: @user.errors.as_json
}, status: :unprocessable_entity
```

## Verification Report Template

```markdown
# Rails Verification Report

**Endpoint:** POST /api/users
**Controller:** Api::UsersController#create
**Time:** TIMESTAMP

## Request

```http
POST /api/users HTTP/1.1
Content-Type: application/json
Authorization: Bearer xxx

{"user": {"email": "test@example.com", "name": "Test"}}
```

## Response

```http
HTTP/1.1 201 Created
Content-Type: application/json

{"id": 1, "email": "test@example.com", "name": "Test"}
```

## Checks

| Check | Status |
|-------|--------|
| Route exists | ✓ |
| Controller action | ✓ |
| Strong params | ✓ |
| Model validation | ✓ |
| Response format | ✓ |
| Status code | ✓ 201 |

## Error Handling

| Case | Status |
|------|--------|
| Missing email | ✓ 422 |
| Invalid email | ✓ 422 |
| Duplicate | ✓ 409 |
| Unauthorized | ✓ 401 |
```
