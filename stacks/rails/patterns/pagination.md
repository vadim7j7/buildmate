# Rails Pagination Patterns

Pagination patterns using Pagy and Kaminari.

---

## 1. Pagy Setup (Recommended)

### Gemfile

```ruby
gem 'pagy'
```

### Initializer

```ruby
# config/initializers/pagy.rb
require 'pagy/extras/metadata'
require 'pagy/extras/overflow'

Pagy::DEFAULT[:items] = 20
Pagy::DEFAULT[:overflow] = :empty_page
```

### Controller Helper

```ruby
# app/controllers/concerns/pagination.rb
# frozen_string_literal: true

module Pagination
  extend ActiveSupport::Concern

  include Pagy::Backend

  private

  def pagy_metadata(pagy)
    {
      current_page: pagy.page,
      per_page: pagy.items,
      total_pages: pagy.pages,
      total_count: pagy.count,
      next_page: pagy.next,
      prev_page: pagy.prev
    }
  end
end
```

---

## 2. Offset-Based Pagination

### Controller

```ruby
# frozen_string_literal: true

module Api
  module V1
    class PostsController < ApplicationController
      include Pagination

      def index
        pagy, posts = pagy(Post.published.order(created_at: :desc))

        render json: {
          data: PostSerializer.new(posts).serialize,
          meta: pagy_metadata(pagy)
        }
      end
    end
  end
end
```

### Response Format

```json
{
  "data": [
    { "id": 1, "title": "Post 1" },
    { "id": 2, "title": "Post 2" }
  ],
  "meta": {
    "current_page": 1,
    "per_page": 20,
    "total_pages": 5,
    "total_count": 100,
    "next_page": 2,
    "prev_page": null
  }
}
```

---

## 3. Cursor-Based Pagination

For large datasets or real-time data, cursor-based pagination is more efficient.

### Concern

```ruby
# app/controllers/concerns/cursor_pagination.rb
# frozen_string_literal: true

module CursorPagination
  extend ActiveSupport::Concern

  DEFAULT_LIMIT = 20
  MAX_LIMIT = 100

  private

  def paginate_with_cursor(scope, order_column: :id, order_direction: :desc)
    limit = [params.fetch(:limit, DEFAULT_LIMIT).to_i, MAX_LIMIT].min
    cursor = params[:cursor]

    records = if cursor
                decoded = decode_cursor(cursor)
                apply_cursor(scope, decoded, order_column, order_direction)
              else
                scope
              end

    records = records.order(order_column => order_direction).limit(limit + 1)
    items = records.to_a

    has_more = items.size > limit
    items = items.first(limit)

    {
      items: items,
      next_cursor: has_more ? encode_cursor(items.last, order_column) : nil,
      has_more: has_more
    }
  end

  def encode_cursor(record, column)
    value = record.send(column)
    Base64.urlsafe_encode64({ column => value, id: record.id }.to_json)
  end

  def decode_cursor(cursor)
    JSON.parse(Base64.urlsafe_decode64(cursor)).symbolize_keys
  rescue StandardError
    nil
  end

  def apply_cursor(scope, cursor, column, direction)
    return scope unless cursor

    value = cursor[column.to_sym]
    id = cursor[:id]

    if direction == :desc
      scope.where("#{column} < ? OR (#{column} = ? AND id < ?)", value, value, id)
    else
      scope.where("#{column} > ? OR (#{column} = ? AND id > ?)", value, value, id)
    end
  end
end
```

### Controller

```ruby
# frozen_string_literal: true

module Api
  module V1
    class FeedController < ApplicationController
      include CursorPagination

      def index
        result = paginate_with_cursor(
          Post.published.includes(:author),
          order_column: :created_at,
          order_direction: :desc
        )

        render json: {
          data: PostSerializer.new(result[:items]).serialize,
          meta: {
            next_cursor: result[:next_cursor],
            has_more: result[:has_more]
          }
        }
      end
    end
  end
end
```

### Response Format

```json
{
  "data": [
    { "id": 100, "title": "Latest Post" },
    { "id": 99, "title": "Second Latest" }
  ],
  "meta": {
    "next_cursor": "eyJjcmVhdGVkX2F0IjoiMjAyNC0wMS0wMVQxMjowMDowMFoiLCJpZCI6OTl9",
    "has_more": true
  }
}
```

---

## 4. Keyset Pagination (Seek Method)

For maximum efficiency with large datasets.

```ruby
# frozen_string_literal: true

module KeysetPagination
  extend ActiveSupport::Concern

  private

  def paginate_keyset(scope, after_id: nil, limit: 20)
    scope = scope.where('id > ?', after_id) if after_id.present?
    scope.order(:id).limit(limit + 1).then do |records|
      items = records.to_a
      has_more = items.size > limit
      items = items.first(limit)

      {
        items: items,
        next_id: has_more ? items.last.id : nil,
        has_more: has_more
      }
    end
  end
end
```

---

## 5. Pagination Presenter

```ruby
# frozen_string_literal: true

module Presenters
  class PaginatedCollection
    def initialize(pagy:, items:, serializer:)
      @pagy = pagy
      @items = items
      @serializer = serializer
    end

    def as_json
      {
        data: @serializer.new(@items).serialize,
        meta: pagination_meta,
        links: pagination_links
      }
    end

    private

    def pagination_meta
      {
        current_page: @pagy.page,
        per_page: @pagy.items,
        total_pages: @pagy.pages,
        total_count: @pagy.count
      }
    end

    def pagination_links
      {
        self: page_url(@pagy.page),
        first: page_url(1),
        last: page_url(@pagy.pages),
        next: @pagy.next ? page_url(@pagy.next) : nil,
        prev: @pagy.prev ? page_url(@pagy.prev) : nil
      }.compact
    end

    def page_url(page)
      # Build URL based on current request
      "#{base_url}?page=#{page}&per_page=#{@pagy.items}"
    end
  end
end
```

---

## 6. GraphQL Pagination (Relay Connections)

```ruby
# frozen_string_literal: true

module Types
  class PostType < Types::BaseObject
    field :id, ID, null: false
    field :title, String, null: false
    field :body, String, null: false
  end
end

module Types
  class QueryType < Types::BaseObject
    field :posts, Types::PostType.connection_type, null: false do
      argument :status, String, required: false
    end

    def posts(status: nil)
      scope = Post.all
      scope = scope.where(status: status) if status
      scope.order(created_at: :desc)
    end
  end
end
```

---

## 7. Filtered Pagination

```ruby
# frozen_string_literal: true

module Api
  module V1
    class PostsController < ApplicationController
      include Pagination

      def index
        scope = Post.all
        scope = apply_filters(scope)
        scope = apply_sorting(scope)

        pagy, posts = pagy(scope)

        render json: {
          data: PostSerializer.new(posts).serialize,
          meta: pagy_metadata(pagy).merge(applied_filters)
        }
      end

      private

      def apply_filters(scope)
        scope = scope.where(status: params[:status]) if params[:status].present?
        scope = scope.where(author_id: params[:author_id]) if params[:author_id].present?
        scope = scope.where('created_at >= ?', params[:from]) if params[:from].present?
        scope = scope.where('created_at <= ?', params[:to]) if params[:to].present?
        scope = scope.search(params[:q]) if params[:q].present?
        scope
      end

      def apply_sorting(scope)
        case params[:sort]
        when 'oldest'
          scope.order(created_at: :asc)
        when 'popular'
          scope.order(views_count: :desc)
        else
          scope.order(created_at: :desc)
        end
      end

      def applied_filters
        {
          filters: {
            status: params[:status],
            author_id: params[:author_id],
            from: params[:from],
            to: params[:to],
            q: params[:q]
          }.compact
        }
      end
    end
  end
end
```

---

## 8. Testing Pagination

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'Posts API Pagination', type: :request do
  describe 'GET /api/v1/posts' do
    before do
      create_list(:post, 25, :published)
    end

    it 'returns paginated results' do
      get '/api/v1/posts', params: { page: 1, per_page: 10 }

      expect(response).to have_http_status(:ok)

      json = JSON.parse(response.body)
      expect(json['data'].size).to eq(10)
      expect(json['meta']['current_page']).to eq(1)
      expect(json['meta']['total_pages']).to eq(3)
      expect(json['meta']['total_count']).to eq(25)
    end

    it 'returns second page' do
      get '/api/v1/posts', params: { page: 2, per_page: 10 }

      json = JSON.parse(response.body)
      expect(json['data'].size).to eq(10)
      expect(json['meta']['current_page']).to eq(2)
      expect(json['meta']['prev_page']).to eq(1)
      expect(json['meta']['next_page']).to eq(3)
    end

    it 'handles out of range pages' do
      get '/api/v1/posts', params: { page: 100, per_page: 10 }

      json = JSON.parse(response.body)
      expect(json['data']).to be_empty
    end
  end
end
```

---

## 9. Performance Considerations

### Avoid COUNT for Large Tables

```ruby
# config/initializers/pagy.rb
Pagy::DEFAULT[:countless] = true  # Skip count query
```

### Use Index for Pagination

```ruby
# db/migrate/xxx_add_pagination_index.rb
add_index :posts, [:created_at, :id], order: { created_at: :desc, id: :desc }
```

### Eager Loading

```ruby
pagy, posts = pagy(
  Post.published
      .includes(:author, :tags)
      .with_attached_featured_image
)
```
