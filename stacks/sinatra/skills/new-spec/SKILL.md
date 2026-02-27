---
name: new-spec
description: Generate an RSpec test file for a Sinatra module
---

# /new-spec

## What This Does

Generates an RSpec spec file for an existing class, detecting the type (model,
service, route, helper) and creating appropriate test patterns with Rack::Test
integration for HTTP tests.

## Usage

```
/new-spec Article                   # Generates spec/models/article_spec.rb
/new-spec ArticlePublishService     # Generates spec/services/article_publish_service_spec.rb
/new-spec "GET /articles"           # Generates spec/requests/articles_spec.rb
```

## How It Works

1. **Detect the class type.** Determine what kind of spec to generate:
   - Class without suffix → model spec
   - Class ending in `Service` → service spec
   - HTTP method + path → request spec (using Rack::Test)
   - Class ending in `Helper` → helper spec

2. **Read the source file.** Analyze the existing class to determine test targets.

3. **Generate the spec file.** Create the spec with:
   - `frozen_string_literal: true`
   - `require 'spec_helper'`
   - For request specs: `include Rack::Test::Methods` and `def app; Sinatra::Application; end`
   - `RSpec.describe` with correct context
   - `subject` for the object under test
   - `let` blocks for dependencies
   - `describe` and `context` blocks

4. **Run the spec.**

   ```bash
   bundle exec rubocop -A <spec_file>
   bundle exec rspec <spec_file>
   ```

## Generated Files

```
spec/<type>/<path>_spec.rb
```
