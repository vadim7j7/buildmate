---
name: new-spec
description: Generate an RSpec test file for a Ruby class
---

# /new-spec

## What This Does

Generates an RSpec spec file for an existing class, detecting the type (model,
service, or general) and creating appropriate test patterns.

## Usage

```
/new-spec Article                   # Generates spec/models/article_spec.rb
/new-spec ArticlePublishService     # Generates spec/services/article_publish_service_spec.rb
/new-spec StringFormatter           # Generates spec/lib/string_formatter_spec.rb
```

## How It Works

1. **Detect the class type.** Determine what kind of spec to generate:
   - Class inheriting `Sequel::Model` → model spec
   - Class ending in `Service` → service spec
   - Other → lib/unit spec

2. **Read the source file.** Analyze the existing class to determine test targets.

3. **Generate the spec file.** Create the spec with:
   - `frozen_string_literal: true`
   - `require 'spec_helper'`
   - `RSpec.describe` with correct context
   - `subject` for the object under test
   - `let` blocks for dependencies
   - `describe` and `context` blocks for each public method

   Model specs touch the database. Wrap every example in a Sequel transaction
   that rolls back, so tests leave no rows behind (put this in `spec/spec_helper.rb`
   once if it is missing):

   ```ruby
   RSpec.configure do |config|
     config.around do |example|
       DB.transaction(rollback: :always, auto_savepoint: true) { example.run }
     end
   end
   ```

   Model spec shape:

   ```ruby
   # frozen_string_literal: true

   require 'spec_helper'

   RSpec.describe Article do
     subject(:article) { described_class.new(title: 'Hello', author_id: author.id) }

     let(:author) { User.create(email: 'a@example.com', name: 'Ann') }

     describe '#validate' do
       it 'is valid with a title and author' do
         expect(article.valid?).to be(true)
       end

       it 'requires a title' do
         article.title = nil
         expect(article.valid?).to be(false)
         expect(article.errors[:title]).not_to be_empty
       end
     end

     describe '.published' do
       it 'returns only published rows' do
         published = described_class.create(title: 'P', author_id: author.id, published: true)
         described_class.create(title: 'D', author_id: author.id)

         expect(described_class.published.all).to eq([published])
       end
     end
   end
   ```

4. **Run the spec.**

   ```bash
   bundle exec rubocop -A <spec_file>
   bundle exec rspec <spec_file>
   ```

## Generated Files

```
spec/<type>/<path>_spec.rb
```
