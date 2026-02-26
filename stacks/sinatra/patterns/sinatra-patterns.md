# Sinatra Code Patterns

Reference patterns for Sinatra web application development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Modular Application Pattern

Always use modular style, never classic Sinatra.

```ruby
# frozen_string_literal: true

require 'sinatra/base'
require 'sinatra/json'

class App < Sinatra::Base
  configure do
    set :root, File.dirname(__FILE__)
    enable :logging
  end

  # Register route modules
  register Routes::Projects
  register Routes::Users

  # Register helper modules
  helpers Helpers::Authentication
  helpers Helpers::Pagination

  # Use middleware
  use Middleware::RequestLogger
  use Middleware::CORS

  # Error handlers
  error Errors::NotFoundError do
    status 404
    json error: env['sinatra.error'].message
  end

  get '/health' do
    json status: 'ok'
  end
end
```

### Rules

- Inherit from `Sinatra::Base`
- Use `register` for route modules
- Use `helpers` for helper modules
- Use `use` for Rack middleware
- Centralize error handlers in the main app class

---

## 2. Route Module Pattern

Organize routes by resource using Sinatra extensions.

```ruby
# frozen_string_literal: true

module Routes
  module Projects
    def self.registered(app)
      app.get '/projects' do
        projects = ProjectService.new.list(
          page: params[:page]&.to_i || 1,
          per_page: params[:per_page]&.to_i || 25
        )
        json projects.map(&:to_h)
      end

      app.post '/projects' do
        data = json_body
        project = ProjectService.new.create(**data.slice(:name, :description))
        status 201
        json project.to_h
      end

      app.get '/projects/:id' do |id|
        project = ProjectService.new.find(id.to_i)
        json project.to_h
      end

      app.patch '/projects/:id' do |id|
        data = json_body
        project = ProjectService.new.update(id.to_i, **data)
        json project.to_h
      end

      app.delete '/projects/:id' do |id|
        ProjectService.new.delete(id.to_i)
        status 204
      end
    end
  end
end
```

### Rules

- One module per resource
- Use `self.registered(app)` pattern
- Delegate business logic to services
- Use `json()` for responses
- Set appropriate status codes

---

## 3. Helper Pattern

Helpers provide shared methods available in route blocks.

```ruby
# frozen_string_literal: true

module Helpers
  module Authentication
    def current_user
      @current_user ||= begin
        token = request.env['HTTP_AUTHORIZATION']&.sub('Bearer ', '')
        raise Errors::AuthorizationError unless token
        User.find_by_token(token)
      end
    end

    def authenticate!
      halt 401, json(error: 'Unauthorized') unless current_user
    end
  end
end
```

---

## 4. Middleware Pattern

Rack middleware for cross-cutting concerns.

```ruby
# frozen_string_literal: true

module Middleware
  class RequestLogger
    def initialize(app)
      @app = app
    end

    def call(env)
      start = Time.now
      status, headers, body = @app.call(env)
      duration = ((Time.now - start) * 1000).round(2)

      AppLogger.info(
        "#{env['REQUEST_METHOD']} #{env['PATH_INFO']} #{status}",
        duration_ms: duration
      )

      [status, headers, body]
    end
  end
end
```

---

## 5. Configuration Pattern

Use Sinatra's `configure` blocks for environment-specific settings.

```ruby
# frozen_string_literal: true

class App < Sinatra::Base
  configure do
    set :root, File.dirname(__FILE__)
    set :database_url, ENV.fetch('DATABASE_URL', 'postgres://localhost/myapp_dev')
    enable :logging
  end

  configure :development do
    enable :reloader
  end

  configure :test do
    set :database_url, 'sqlite::memory:'
  end

  configure :production do
    disable :show_exceptions
    enable :dump_errors
  end
end
```

---

## 6. Testing Pattern

```ruby
# frozen_string_literal: true

require 'spec_helper'
require 'rack/test'

RSpec.describe Routes::Projects do
  include Rack::Test::Methods

  def app
    App
  end

  describe 'GET /projects' do
    it 'returns a list of projects' do
      create(:project, name: 'Test')

      get '/projects'

      expect(last_response.status).to eq(200)
      data = JSON.parse(last_response.body)
      expect(data).to be_an(Array)
      expect(data.first['name']).to eq('Test')
    end
  end

  describe 'POST /projects' do
    it 'creates a new project' do
      post '/projects', { name: 'New Project' }.to_json,
           'CONTENT_TYPE' => 'application/json'

      expect(last_response.status).to eq(201)
      data = JSON.parse(last_response.body)
      expect(data['name']).to eq('New Project')
    end
  end

  describe 'GET /projects/:id' do
    it 'returns 404 for missing project' do
      get '/projects/99999'
      expect(last_response.status).to eq(404)
    end
  end
end
```
