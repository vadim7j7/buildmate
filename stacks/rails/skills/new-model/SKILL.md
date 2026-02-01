---
name: new-model
description: Generate an ActiveRecord model with associations, validations, scopes, and spec
---

# /new-model

## What This Does

Generates a new ActiveRecord model following the project's model pattern: associations,
validations, enums, scopes, and callbacks in consistent order. Also generates the
migration, factory, and model spec.

## Usage

```
/new-model Candidate                  # Creates Candidate model
/new-model ProfileSkill               # Creates ProfileSkill join model
/new-model Experience                 # Creates Experience model
```

## How It Works

1. **Read reference patterns.** Load the model pattern from:
   - `skills/new-model/references/model-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-ruby.md`

2. **Determine the model name and attributes.** Parse the argument and ask for
   or infer attributes based on the model name and context.

3. **Generate the migration.** Create a migration file for the new table:

   ```bash
   bundle exec rails generate migration Create<ModelName>
   ```

   Then edit the migration with appropriate columns, indices, and foreign keys.

4. **Generate the model file.** Create the model with:
   - `frozen_string_literal: true`
   - Associations (belongs_to, has_many, has_one)
   - Validations (presence, uniqueness, format)
   - Enums (if applicable)
   - Scopes (active, recent, search)
   - Callbacks (before_validation, after_create)
   - YARD documentation

5. **Generate the factory.** Create a FactoryBot factory with:
   - Required attributes using Faker
   - Sequences for unique fields
   - Traits for variations

6. **Generate the model spec.** Create the spec with:
   - Association tests (Shoulda Matchers)
   - Validation tests
   - Scope tests with actual database queries
   - Callback tests

7. **Run migrations and quality checks.**

   ```bash
   rails db:migrate
   bundle exec rubocop -A <generated_files>
   bundle exec rspec spec/models/<model>_spec.rb
   ```

## Generated Files

```
db/migrate/YYYYMMDDHHMMSS_create_<table_name>.rb
app/models/<model_name>.rb
spec/models/<model_name>_spec.rb
spec/factories/<table_name>.rb
```
