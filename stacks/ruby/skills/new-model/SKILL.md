---
name: new-model
description: Generate a Sequel model with migration and spec
---

# /new-model

## What This Does

Generates a Sequel model (the stack's ORM) with migration file, model class, and
RSpec spec. This is the generic Ruby version — framework children override with
their own conventions.

If the project uses MongoDB (`--db=mongodb`), follow `.claude/patterns/mongoid.md` instead:
Mongoid models declare fields in the class and have no migrations.

## Usage

```
/new-model Article                  # Creates Article model
/new-model UserProfile              # Creates UserProfile model
```

## How It Works

1. **Read reference patterns.** Load the model pattern from:
   - `.claude/patterns/backend-patterns.md`
   - `.claude/styles/backend-ruby.md`

2. **Determine the model name and attributes.** Parse the argument and infer
   attributes based on the model name and context.

3. **Generate the migration.** Create a Sequel migration in `db/migrations/`
   (timestamp-prefixed so Sequel's TimestampMigrator orders it):

   ```ruby
   # db/migrations/YYYYMMDDHHMMSS_create_articles.rb
   # frozen_string_literal: true

   Sequel.migration do
     change do
       create_table(:articles) do
         primary_key :id
         foreign_key :author_id, :users, null: false, on_delete: :cascade
         String :title, null: false
         String :body, text: true
         TrueClass :published, null: false, default: false
         DateTime :created_at, null: false, default: Sequel::CURRENT_TIMESTAMP
         DateTime :updated_at, null: false, default: Sequel::CURRENT_TIMESTAMP

         index :author_id
       end
     end
   end
   ```

4. **Generate the model file.** Create the model with:
   - `frozen_string_literal: true`
   - Inheriting from `Sequel::Model`
   - Associations (`many_to_one`, `one_to_many`, `many_to_many`)
   - Validations in `def validate` (call `super` first), or the
     `validation_helpers` plugin (`validates_presence`, `validates_unique`)
   - Query scopes in `dataset_module`
   - `plugin :timestamps, update_on_create: true` to fill `created_at`/`updated_at`
   - YARD documentation

   ```ruby
   # frozen_string_literal: true

   # A published or draft article written by a user.
   class Article < Sequel::Model
     plugin :timestamps, update_on_create: true
     plugin :validation_helpers

     many_to_one :author, class: :User

     dataset_module do
       def published
         where(published: true)
       end
     end

     def validate
       super
       validates_presence %i[title author_id]
       validates_max_length 200, :title
     end
   end
   ```

5. **Generate the spec file.** Create RSpec tests with:
   - Validation tests (`expect(article.valid?).to be(false)` and `article.errors[:title]`)
   - Association tests (create the parent row, check `article.author`)
   - Dataset method tests (`Article.published`)
   - Each example wrapped in a rolled-back transaction (see `/new-spec`)

6. **Run quality checks.**

   ```bash
   bundle exec sequel -m db/migrations "$DATABASE_URL"   # or: bundle exec rake db:migrate
   bundle exec rubocop -A <generated_files>
   bundle exec rspec <spec_file>
   ```

## Generated Files

```
db/migrations/YYYYMMDDHHMMSS_create_<table_name>.rb
app/models/<model_name>.rb  (or lib/models/<model_name>.rb)
spec/models/<model_name>_spec.rb
```
