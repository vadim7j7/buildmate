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
   - Class inheriting `Sequel::Model` → model spec
   - Class ending in `Service` → service spec
   - HTTP method + path → request spec (using Rack::Test)
   - Class ending in `Helper` → helper spec

2. **Read the source file.** Analyze the existing class to determine test targets.

3. **Generate the spec file.** Create the spec with:
   - `frozen_string_literal: true`
   - `require 'spec_helper'`
   - For request specs: `include Rack::Test::Methods` and `def app = App` (the modular
     `class App < Sinatra::Base`, not `Sinatra::Application`)
   - `RSpec.describe` with correct context
   - `subject` for the object under test
   - `let` blocks for dependencies
   - `describe` and `context` blocks

   Model and request specs touch the database (Sequel). Wrap every example in a
   transaction that rolls back (add to `spec/spec_helper.rb` once if missing):

   ```ruby
   RSpec.configure do |config|
     config.around do |example|
       DB.transaction(rollback: :always, auto_savepoint: true) { example.run }
     end
   end
   ```

   Request spec shape:

   ```ruby
   # frozen_string_literal: true

   require 'spec_helper'

   RSpec.describe 'GET /articles' do
     include Rack::Test::Methods

     def app = App

     it 'lists articles' do
       author = User.create(email: 'a@example.com', name: 'Ann')
       Article.create(title: 'Hello', author_id: author.id)

       get '/articles'

       expect(last_response.status).to eq(200)
       expect(JSON.parse(last_response.body).first['title']).to eq('Hello')
     end
   end
   ```

   Model specs use `Article.create(...)`, `article.valid?` and `article.errors[:field]`
   (Sequel's API, not ActiveRecord's).

4. **Run the spec.**

   ```bash
   bundle exec rubocop -A <spec_file>
   bundle exec rspec <spec_file>
   ```

## Generated Files

```
spec/<type>/<path>_spec.rb
```
