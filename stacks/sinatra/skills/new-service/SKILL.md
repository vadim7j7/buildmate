---
name: new-service
description: Generate a service object with spec file for Sinatra
---

# /new-service

## What This Does

Generates a service object encapsulating business logic, with a single `call`
method and corresponding RSpec spec.

## Usage

```
/new-service ArticlePublish          # Creates ArticlePublishService
/new-service UserRegistration        # Creates UserRegistrationService
```

## How It Works

1. **Read reference patterns.** Load the service pattern from:
   - `patterns/sinatra-patterns.md`
   - `styles/backend-ruby.md`

2. **Determine service name.** Parse the argument to determine the class name:
   - `ArticlePublish` becomes `ArticlePublishService` in `app/services/article_publish_service.rb`

3. **Generate the service file.** Create the service with:
   - `frozen_string_literal: true`
   - YARD documentation
   - `initialize` with keyword arguments
   - `call` method with guard clause
   - Private `attr_reader` and helper methods

4. **Generate the spec file.** Create the spec with:
   - `subject(:service)` with constructor
   - `let` blocks for dependencies
   - `describe '#call'` with context blocks for happy path and edge cases

5. **Run quality checks.**

   ```bash
   bundle exec rubocop -A <generated_files>
   bundle exec rspec <spec_file>
   ```

## Generated Files

```
app/services/<service_name>.rb  (or services/<service_name>.rb)
spec/services/<service_name>_spec.rb
```
