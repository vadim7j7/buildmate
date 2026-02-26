---
name: new-helper
description: Generate a Sinatra helper module with shared methods
---

# /new-helper

## What This Does

Generates a Sinatra helper module that provides shared methods available in route blocks.
Registers the helper in the main application.

## Usage

```
/new-helper authentication    # Creates helpers/authentication.rb
/new-helper pagination        # Creates helpers/pagination.rb
/new-helper json_response     # Creates helpers/json_response.rb
```

## How It Works

1. **Read reference patterns.** Load the helper pattern from:
   - `patterns/sinatra-patterns.md`
   - `styles/backend-ruby.md`

2. **Determine helper name.** Parse the argument to determine the module name and file path.

3. **Generate the helper module.** Create the helper with:
   - `frozen_string_literal: true`
   - Module under `Helpers` namespace
   - YARD documentation on all public methods
   - Appropriate methods based on the helper name

4. **Generate the test file.** Create RSpec tests for the helper.

5. **Register the helper.** Add `helpers Helpers::HelperName` to `app.rb`.

6. **Run quality checks.**

   ```bash
   bundle exec rubocop <generated_files>
   bundle exec rspec <spec_files>
   ```

7. **Report results.** Show the generated files.

## Generated Files

```
app/helpers/<helper_name>.rb
spec/helpers/<helper_name>_spec.rb
```
