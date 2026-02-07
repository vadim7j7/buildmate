---
name: new-concern
description: Generate a model or controller concern with spec file
---

# /new-concern

## What This Does

Generates a new Rails concern (shared module) for either models or controllers.
Concerns encapsulate reusable behavior like soft deletes, sluggable, searchable,
or controller authentication logic.

## Usage

```
/new-concern Sluggable                    # Creates Sluggable model concern
/new-concern Searchable for models        # Creates Searchable model concern
/new-concern Authenticatable for controllers  # Creates controller concern
/new-concern SoftDeletable                # Creates SoftDeletable model concern
```

## How It Works

1. **Determine concern type.** Parse the argument to identify:
   - Concern name (e.g., `Sluggable`, `Searchable`)
   - Target: `models` (default) or `controllers`

2. **Read reference patterns.** Load patterns from:
   - `skills/new-concern/references/concern-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-ruby.md`

3. **Generate the concern file.** Create the concern with:
   - `frozen_string_literal: true`
   - `extend ActiveSupport::Concern`
   - `included` block for class-level macros
   - `class_methods` block for class methods
   - Instance methods
   - YARD documentation

4. **Generate the spec file.** Create the spec with:
   - Shared examples for the concern behavior
   - Test model that includes the concern
   - Tests for all public methods
   - Edge cases and error conditions

5. **Run quality checks.**

   ```bash
   bundle exec rubocop -A app/models/concerns/<name>.rb spec/models/concerns/<name>_spec.rb
   bundle exec rspec spec/models/concerns/<name>_spec.rb
   ```

6. **Report results.** Show the generated files and test results.

## Generated Files

For model concerns:
```
app/models/concerns/<concern_name>.rb
spec/models/concerns/<concern_name>_spec.rb
```

For controller concerns:
```
app/controllers/concerns/<concern_name>.rb
spec/controllers/concerns/<concern_name>_spec.rb
```

## Example Output

For `/new-concern Sluggable`:

**Concern:** `app/models/concerns/sluggable.rb`
```ruby
# frozen_string_literal: true

# Provides URL-friendly slug generation from a source attribute.
#
# @example Include in a model
#   class Post < ApplicationRecord
#     include Sluggable
#     sluggable_attribute :title
#   end
#
module Sluggable
  extend ActiveSupport::Concern

  included do
    before_validation :generate_slug, on: :create

    validates :slug, presence: true, uniqueness: true

    class_attribute :slug_source_attribute, default: :name
  end

  class_methods do
    # Configure which attribute to generate the slug from.
    #
    # @param attribute [Symbol] the source attribute
    def sluggable_attribute(attribute)
      self.slug_source_attribute = attribute
    end
  end

  # Find a record by its slug.
  #
  # @return [String] the URL-friendly slug
  def to_param
    slug
  end

  private

  def generate_slug
    return if slug.present?

    source = send(self.class.slug_source_attribute)
    self.slug = source.to_s.parameterize
    ensure_unique_slug
  end

  def ensure_unique_slug
    base_slug = slug
    counter = 1
    while self.class.exists?(slug: slug)
      self.slug = "#{base_slug}-#{counter}"
      counter += 1
    end
  end
end
```

**Spec:** `spec/models/concerns/sluggable_spec.rb`

## Rules

- Use `extend ActiveSupport::Concern` (not `include`)
- Put class-level macros in `included` block
- Put class methods in `class_methods` block
- Keep concerns focused on a single responsibility
- Use `class_attribute` for configurable options
- Document usage with `@example` in YARD docs
