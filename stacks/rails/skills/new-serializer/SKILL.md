---
name: new-serializer
description: Generate an Alba or JSON:API serializer with spec file
---

# /new-serializer

## What This Does

Generates a serializer for transforming model data into JSON API responses.
Supports Alba (default) or jsonapi-serializer. Creates the serializer class
and corresponding spec file.

## Usage

```
/new-serializer User                    # Creates UserSerializer
/new-serializer Post                    # Creates PostSerializer
/new-serializer Admin::Report           # Creates Admin::ReportSerializer
```

## How It Works

1. **Read reference patterns.** Load serializer patterns from:
   - `skills/new-serializer/references/serializer-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-ruby.md`

2. **Determine serializer name.** Parse the argument to determine:
   - Serializer class name (e.g., `UserSerializer`)
   - Associated model (e.g., `User`)
   - File path (e.g., `app/serializers/user_serializer.rb`)

3. **Analyze the model.** Read the model to understand:
   - Attributes to serialize
   - Associations to include
   - Computed attributes (methods to expose)

4. **Generate the serializer file.** Create the serializer with:
   - `frozen_string_literal: true`
   - Attribute definitions
   - Association definitions
   - Computed/derived attributes

5. **Generate the spec file.** Create the spec with:
   - Attribute presence tests
   - Association tests
   - Computed attribute tests

6. **Run quality checks.**

   ```bash
   bundle exec rubocop -A app/serializers/<path>.rb spec/serializers/<path>_spec.rb
   bundle exec rspec spec/serializers/<path>_spec.rb
   ```

7. **Report results.** Show generated files.

## Generated Files

```
app/serializers/<model>_serializer.rb
spec/serializers/<model>_serializer_spec.rb
```

## Example Output

For `/new-serializer Post` (Alba):

**Serializer:** `app/serializers/post_serializer.rb`
```ruby
# frozen_string_literal: true

# Serializes Post for API responses.
#
# @example Basic usage
#   PostSerializer.new(post).serialize
#
# @example With root key
#   PostSerializer.new(post, root_key: :post).serialize
#
class PostSerializer
  include Alba::Resource

  attributes :id, :title, :body, :published_at, :created_at, :updated_at

  attribute :excerpt do |post|
    post.body.truncate(200)
  end

  attribute :reading_time do |post|
    words = post.body.split.size
    (words / 200.0).ceil
  end

  one :author, resource: UserSerializer
  many :comments, resource: CommentSerializer

  # Only include if published
  attribute :published do |post|
    post.published_at.present?
  end
end
```

For `/new-serializer Post` (jsonapi-serializer):

**Serializer:** `app/serializers/post_serializer.rb`
```ruby
# frozen_string_literal: true

# Serializes Post for JSON:API responses.
#
# @example Basic usage
#   PostSerializer.new(post).serializable_hash
#
class PostSerializer
  include JSONAPI::Serializer

  set_type :posts
  set_id :id

  attributes :title, :body, :published_at, :created_at, :updated_at

  attribute :excerpt do |post|
    post.body.truncate(200)
  end

  attribute :reading_time do |post|
    words = post.body.split.size
    (words / 200.0).ceil
  end

  belongs_to :author, serializer: UserSerializer
  has_many :comments, serializer: CommentSerializer

  link :self do |post|
    Rails.application.routes.url_helpers.api_v1_post_url(post)
  end
end
```

**Spec:** `spec/serializers/post_serializer_spec.rb`

## Rules

- One serializer per model
- Keep computed attributes lightweight (no N+1 queries)
- Use nested serializers for associations
- Avoid exposing sensitive attributes (passwords, tokens)
- Use `attribute` blocks for computed values
- Document serializer usage with `@example`
- Test all attributes and associations
