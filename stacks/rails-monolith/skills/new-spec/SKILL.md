---
name: new-spec
description: Generate an RSpec test file for a model, service, controller, or presenter
---

# /new-spec

## What This Does

Generates an RSpec spec file for an existing class, detecting the type (model, service,
controller, presenter, job) and creating appropriate test patterns with FactoryBot
integration and comprehensive coverage.

## Usage

```
/new-spec ProfileService              # Generates spec/services/profile_service_spec.rb
/new-spec Profile                     # Generates spec/models/profile_spec.rb
/new-spec ProfilesController          # Generates spec/requests/profiles_spec.rb
/new-spec ProfilePresenter            # Generates spec/presenters/profile_presenter_spec.rb
/new-spec Sync::AirtableImportJob     # Generates spec/jobs/sync/airtable_import_job_spec.rb
```

## How It Works

1. **Read reference patterns.** Load the spec patterns from:
   - `skills/new-spec/references/spec-examples.md`
   - `skills/test/references/rspec-patterns.md`
   - `skills/test/references/factory-patterns.md`

2. **Detect the class type.** Determine what kind of spec to generate:
   - Class ending in `Service` -> service spec
   - Class ending in `Controller` -> request spec
   - Class ending in `Presenter` -> presenter spec
   - Class ending in `Job` -> job spec
   - Otherwise -> model spec

3. **Read the source file.** Analyze the existing class to determine:
   - Associations (for model specs)
   - Validations (for model specs)
   - Constructor arguments (for service/presenter specs)
   - Actions and routes (for request specs)
   - Queue configuration (for job specs)

4. **Generate the spec file.** Create the spec with appropriate patterns:
   - `frozen_string_literal: true`
   - `require 'rails_helper'`
   - `RSpec.describe` with correct type tag
   - `subject` for the object under test
   - `let` blocks for dependencies using FactoryBot
   - `describe` and `context` blocks for all test scenarios

5. **Ensure factory exists.** Check `spec/factories/` for a matching factory.
   If missing, create one.

6. **Run the spec.**

   ```bash
   bundle exec rubocop -A spec/<path>_spec.rb
   bundle exec rspec spec/<path>_spec.rb
   ```

## Generated Files

```
spec/<type>/<path>_spec.rb
spec/factories/<model>.rb  (if missing)
```
