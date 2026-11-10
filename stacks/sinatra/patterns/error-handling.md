# Sinatra Error Handling and JSON API Patterns

Every response from the API is JSON, including errors, and every error has the
same shape. Routes raise domain errors; the app class maps them to HTTP once.

---

## 1. Error Envelope

```json
{ "error": { "code": "validation_failed", "message": "Validation failed", "details": { "name": ["is not present"] } } }
```

- `code`: stable, machine-readable, snake_case (clients branch on it)
- `message`: human-readable, safe to show; never a stack trace or SQL
- `details`: optional (field errors for 422)

---

## 2. Error Classes

```ruby
# frozen_string_literal: true

# lib/errors.rb
module Errors
  class AppError < StandardError
    def status = 500
    def code = "internal_error"
    def details = nil
  end

  class BadRequestError < AppError
    def status = 400
    def code = "bad_request"
  end

  class AuthorizationError < AppError
    def status = 401
    def code = "unauthorized"
  end

  class ForbiddenError < AppError
    def status = 403
    def code = "forbidden"
  end

  class NotFoundError < AppError
    def status = 404
    def code = "not_found"
  end

  class ValidationError < AppError
    def initialize(details, message = "Validation failed")
      @details = details
      super(message)
    end

    attr_reader :details

    def status = 422
    def code = "validation_failed"
  end
end
```

---

## 3. Mapping Errors in the App

```ruby
# frozen_string_literal: true

class App < Sinatra::Base
  configure do
    set :show_exceptions, false  # no HTML debug pages, even in development
    set :raise_errors, false     # let the handlers below answer (also in test)
  end

  before { content_type :json }

  helpers do
    def error_response(status_code, code, message, details = nil)
      body = { code:, message: }
      body[:details] = details if details
      halt status_code, JSON.generate(error: body)
    end
  end

  error Errors::AppError do
    e = env["sinatra.error"]
    error_response(e.status, e.code, e.message, e.details)
  end

  error Sequel::NoMatchingRow do        # Model.with_pk!(id) / first! found nothing
    error_response(404, "not_found", "Not found")
  end

  error Sequel::ValidationFailed do
    e = env["sinatra.error"]
    error_response(422, "validation_failed", "Validation failed", e.errors)
  end

  not_found do                          # unknown route
    error_response(404, "not_found", "No route for #{request.request_method} #{request.path_info}")
  end

  error StandardError do                # last resort: log it, hide it
    e = env["sinatra.error"]
    logger.error("#{e.class}: #{e.message}\n#{e.backtrace&.first(10)&.join("\n")}")
    error_response(500, "internal_error", "Something went wrong")
  end
end
```

Sinatra checks error handlers from the most specific class up, so the
`StandardError` handler only catches what the others don't.

---

## 4. Request Bodies

```ruby
# frozen_string_literal: true

module Helpers
  module JsonBody
    # Parsed JSON body with symbol keys; 400 on malformed JSON or a non-object.
    def json_body
      @json_body ||= begin
        data = JSON.parse(request.body.read, symbolize_names: true)
        raise Errors::BadRequestError, "Body must be a JSON object" unless data.is_a?(Hash)

        data
      rescue JSON::ParserError
        raise Errors::BadRequestError, "Malformed JSON"
      end
    end

    # Whitelist keys before passing data to a service (the Sinatra strong params).
    def permitted(data, *keys)
      data.slice(*keys)
    end
  end
end
```

```ruby
app.post "/projects" do
  project = ProjectService.new.create(**permitted(json_body, :name, :description))
  status 201
  json project.to_h
end
```

Never pass `json_body` straight to `Model.create`: a client could set `admin`,
`user_id` or any other column.

---

## 5. Status Codes

| Situation | Status |
|-----------|--------|
| Read OK / update OK | 200 with the resource |
| Created | 201 with the resource (and `Location` header if useful) |
| Deleted / nothing to return | 204, empty body |
| Malformed JSON, bad query param | 400 |
| Missing or invalid credentials | 401 |
| Authenticated but not allowed | 403 (or 404 to hide existence) |
| Validation failed | 422 with `details` |
| Unexpected exception | 500, generic message, logged |

---

## 6. Testing Errors

```ruby
it "returns 422 with field errors" do
  post "/projects", { name: "" }.to_json, "CONTENT_TYPE" => "application/json"

  expect(last_response.status).to eq(422)
  body = JSON.parse(last_response.body)
  expect(body.dig("error", "code")).to eq("validation_failed")
  expect(body.dig("error", "details")).to have_key("name")
end

it "returns 400 on malformed JSON" do
  post "/projects", "{not json", "CONTENT_TYPE" => "application/json"
  expect(last_response.status).to eq(400)
end
```

Cover for each new route: success, 404 for a missing record, 422 for invalid
input, 401 without credentials (when protected).
