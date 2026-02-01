---
name: new-service
description: Generate a namespaced service object with spec file
---

# /new-service

## What This Does

Generates a new service object following the project's service pattern: namespaced
under a module, inheriting from `ApplicationService`, with keyword arguments and a
single `call` method. Also generates the corresponding RSpec spec file.

## Usage

```
/new-service UserSync                    # Creates Users::SyncService
/new-service BulkImport::Profiles        # Creates BulkImport::ProfilesService
/new-service Airtable::CompanySync       # Creates Airtable::CompanySyncService
```

## How It Works

1. **Read reference patterns.** Load the service pattern from:
   - `skills/new-service/references/service-examples.md`
   - `skills/new-service/references/service-structure.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-ruby.md`

2. **Determine namespace and class name.** Parse the argument to determine the
   module namespace and class name:
   - `UserSync` becomes `Users::SyncService` in `app/services/users/sync_service.rb`
   - `BulkImport::Profiles` becomes `BulkImport::ProfilesService` in
     `app/services/bulk_import/profiles_service.rb`

3. **Generate the service file.** Create the service file with:
   - `frozen_string_literal: true`
   - Module namespace
   - YARD documentation
   - `ApplicationService` inheritance
   - `initialize` with keyword arguments
   - `call` method with guard clause
   - Private `attr_reader` and helper methods

4. **Generate the spec file.** Create the spec file with:
   - Matching namespace and describe block
   - `subject(:service)` with constructor
   - `let` blocks for dependencies
   - `describe '#call'` with context blocks for happy path, edge cases, and errors

5. **Run quality checks.**

   ```bash
   bundle exec rubocop -A app/services/<path>.rb spec/services/<path>_spec.rb
   bundle exec rspec spec/services/<path>_spec.rb
   ```

6. **Report results.** Show the generated files and test results.

## Generated Files

```
app/services/<namespace>/<service_name>.rb
spec/services/<namespace>/<service_name>_spec.rb
```

## Example Output

For `/new-service BulkImport::Profiles`:

**Service:** `app/services/bulk_import/profiles_service.rb`
**Spec:** `spec/services/bulk_import/profiles_service_spec.rb`
