---
name: new-route
description: Generate a Sinatra route module with CRUD endpoints and service
---

# /new-route

## What This Does

Generates a Sinatra route module with CRUD endpoints, along with the corresponding
service class and a test file. Registers the route module in the main app.

## Usage

```
/new-route projects           # Creates routes/projects.rb, services/project_service.rb
/new-route users              # Creates routes/users.rb, services/user_service.rb
/new-route admin/settings     # Creates routes/admin/settings.rb (nested path)
```

## How It Works

1. **Read reference patterns.** Load the route pattern from:
   - `patterns/sinatra-patterns.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-ruby.md`

2. **Determine resource name.** Parse the argument to determine the resource name,
   file paths, and URL prefix.

3. **Generate the route module.** Create the route module with:
   - `frozen_string_literal: true`
   - `self.registered(app)` pattern
   - CRUD routes: list, create, get, update, delete
   - JSON body parsing
   - Service delegation

4. **Generate the service file.** Create the service class with CRUD operations.

5. **Generate the test file.** Create RSpec tests with `Rack::Test`.

6. **Register the route module.** Add `register Routes::ResourceName` to `app.rb`.

7. **Run quality checks.**

   ```bash
   bundle exec rubocop <generated_files>
   bundle exec rspec <spec_files>
   ```

8. **Report results.** Show the generated files.

## Generated Files

```
app/routes/<resource>.rb
app/services/<resource>_service.rb
spec/routes/<resource>_spec.rb
```
