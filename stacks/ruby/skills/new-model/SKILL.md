---
name: new-model
description: Generate an ActiveRecord model with migration and spec
---

# /new-model

## What This Does

Generates an ActiveRecord model with migration file, model class, and RSpec spec.
This is the generic Ruby version — framework children (Rails, Sinatra) override with
their own conventions.

## Usage

```
/new-model Article                  # Creates Article model
/new-model UserProfile              # Creates UserProfile model
```

## How It Works

1. **Read reference patterns.** Load the model pattern from:
   - `styles/backend-ruby.md`

2. **Determine the model name and attributes.** Parse the argument and infer
   attributes based on the model name and context.

3. **Generate the migration.** Create a migration file in `db/migrate/`:

   ```ruby
   # db/migrate/YYYYMMDDHHMMSS_create_articles.rb
   class CreateArticles < ActiveRecord::Migration[7.0]
     def change
       create_table :articles do |t|
         t.string :title, null: false
         t.text :body
         t.timestamps
       end
     end
   end
   ```

4. **Generate the model file.** Create the model with:
   - `frozen_string_literal: true`
   - Inheriting from `ActiveRecord::Base` (or `ApplicationRecord` if available)
   - Associations, validations, scopes
   - YARD documentation

5. **Generate the spec file.** Create RSpec tests with:
   - Validation tests
   - Association tests
   - Scope tests

6. **Run quality checks.**

   ```bash
   bundle exec rake db:migrate
   bundle exec rubocop -A <generated_files>
   bundle exec rspec <spec_file>
   ```

## Generated Files

```
db/migrate/YYYYMMDDHHMMSS_create_<table_name>.rb
app/models/<model_name>.rb  (or models/<model_name>.rb)
spec/models/<model_name>_spec.rb
```
