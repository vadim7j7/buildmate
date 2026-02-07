# Rails Caching Patterns

Caching patterns using Redis for performance optimization.

---

## 1. Cache Configuration

```ruby
# config/environments/production.rb
config.cache_store = :redis_cache_store, {
  url: ENV['REDIS_URL'],
  namespace: 'myapp_cache',
  expires_in: 1.day,
  race_condition_ttl: 10.seconds,
  error_handler: ->(method:, returning:, exception:) {
    Rails.logger.error("Redis cache error: #{exception.message}")
    Sentry.capture_exception(exception)
  }
}
```

---

## 2. Low-Level Caching

```ruby
# frozen_string_literal: true

class Post < ApplicationRecord
  def cached_comments_count
    Rails.cache.fetch(comments_count_cache_key, expires_in: 1.hour) do
      comments.count
    end
  end

  def expire_comments_cache
    Rails.cache.delete(comments_count_cache_key)
  end

  private

  def comments_count_cache_key
    "posts/#{id}/comments_count"
  end
end

# Expire on comment changes
class Comment < ApplicationRecord
  belongs_to :post, touch: true

  after_commit :expire_post_cache

  private

  def expire_post_cache
    post.expire_comments_cache
  end
end
```

---

## 3. Russian Doll Caching

```ruby
# frozen_string_literal: true

class Post < ApplicationRecord
  belongs_to :author
  has_many :comments

  # Auto-update cache key when updated
  def cache_key_with_version
    "#{cache_key}-#{updated_at.to_i}"
  end
end

# View caching
# app/views/posts/index.html.erb
<% cache ['posts', @posts.maximum(:updated_at)] do %>
  <% @posts.each do |post| %>
    <% cache post do %>
      <%= render post %>
    <% end %>
  <% end %>
<% end %>
```

---

## 4. API Response Caching

```ruby
# frozen_string_literal: true

module Api
  module V1
    class PostsController < ApplicationController
      def index
        posts = cached_posts

        render json: {
          data: PostSerializer.new(posts).serialize,
          cached_at: cache_timestamp
        }
      end

      def show
        post = cached_post

        render json: PostSerializer.new(post).serialize
      end

      private

      def cached_posts
        Rails.cache.fetch(posts_cache_key, expires_in: 15.minutes) do
          Post.published.includes(:author).order(created_at: :desc).limit(50).to_a
        end
      end

      def cached_post
        Rails.cache.fetch(post_cache_key, expires_in: 1.hour) do
          Post.includes(:author, :comments).find(params[:id])
        end
      end

      def posts_cache_key
        ['api', 'v1', 'posts', Post.maximum(:updated_at)&.to_i].join('/')
      end

      def post_cache_key
        ['api', 'v1', 'posts', params[:id], @post&.updated_at&.to_i].join('/')
      end

      def cache_timestamp
        Rails.cache.read("#{posts_cache_key}/cached_at") || Time.current.iso8601
      end
    end
  end
end
```

---

## 5. Query Result Caching

```ruby
# frozen_string_literal: true

module Cacheable
  extend ActiveSupport::Concern

  class_methods do
    def cached_find(id, expires_in: 1.hour)
      Rails.cache.fetch("#{model_name.cache_key}/#{id}", expires_in: expires_in) do
        find(id)
      end
    end

    def cached_count(scope_name = :all, expires_in: 5.minutes)
      Rails.cache.fetch("#{model_name.cache_key}/count/#{scope_name}", expires_in: expires_in) do
        public_send(scope_name).count
      end
    end
  end
end

class Post < ApplicationRecord
  include Cacheable

  after_commit :invalidate_caches

  private

  def invalidate_caches
    Rails.cache.delete("#{self.class.model_name.cache_key}/#{id}")
    Rails.cache.delete_matched("#{self.class.model_name.cache_key}/count/*")
  end
end
```

---

## 6. Memoization + Caching

```ruby
# frozen_string_literal: true

class Dashboard
  include ActiveModel::Model

  def initialize(user:)
    @user = user
  end

  def stats
    @stats ||= fetch_cached_stats
  end

  def recent_activity
    @recent_activity ||= fetch_cached_activity
  end

  private

  attr_reader :user

  def fetch_cached_stats
    Rails.cache.fetch(stats_cache_key, expires_in: 5.minutes) do
      {
        posts_count: user.posts.count,
        comments_count: user.comments.count,
        followers_count: user.followers.count,
        following_count: user.following.count
      }
    end
  end

  def fetch_cached_activity
    Rails.cache.fetch(activity_cache_key, expires_in: 2.minutes) do
      user.activities.recent.limit(10).to_a
    end
  end

  def stats_cache_key
    "dashboard/#{user.id}/stats/#{user.updated_at.to_i}"
  end

  def activity_cache_key
    "dashboard/#{user.id}/activity"
  end
end
```

---

## 7. Cache Warming

```ruby
# frozen_string_literal: true

class CacheWarmerJob < ApplicationJob
  queue_as :low

  def perform
    warm_popular_posts
    warm_user_counts
    warm_homepage_data
  end

  private

  def warm_popular_posts
    Post.published.popular.limit(100).each do |post|
      Rails.cache.fetch("posts/#{post.id}", expires_in: 1.hour) { post }
    end
  end

  def warm_user_counts
    User.active.find_each do |user|
      Rails.cache.fetch("users/#{user.id}/stats", expires_in: 30.minutes) do
        {
          posts_count: user.posts.count,
          followers_count: user.followers.count
        }
      end
    end
  end

  def warm_homepage_data
    Rails.cache.fetch('homepage/featured', expires_in: 1.hour) do
      Post.featured.includes(:author).limit(10).to_a
    end
  end
end
```

---

## 8. HTTP Caching

```ruby
# frozen_string_literal: true

module Api
  module V1
    class PostsController < ApplicationController
      def show
        @post = Post.find(params[:id])

        if stale?(etag: @post, last_modified: @post.updated_at)
          render json: PostSerializer.new(@post).serialize
        end
      end

      def index
        @posts = Post.published.order(created_at: :desc)

        # Cache for 5 minutes on CDN, revalidate with server
        expires_in 5.minutes, public: true, stale_while_revalidate: 1.minute

        render json: PostSerializer.new(@posts).serialize
      end
    end
  end
end
```

---

## 9. Cache Invalidation Service

```ruby
# frozen_string_literal: true

module Cache
  class InvalidationService < ApplicationService
    def initialize(record)
      @record = record
      @keys_to_delete = []
    end

    def call
      collect_keys
      delete_keys
      success(deleted_count: keys_to_delete.size)
    end

    private

    attr_reader :record, :keys_to_delete

    def collect_keys
      # Direct record cache
      keys_to_delete << record_cache_key

      # Related caches
      collect_association_keys
      collect_counter_keys
    end

    def record_cache_key
      "#{record.class.model_name.cache_key}/#{record.id}"
    end

    def collect_association_keys
      record.class.reflect_on_all_associations(:belongs_to).each do |assoc|
        if (related = record.public_send(assoc.name))
          keys_to_delete << "#{related.class.model_name.cache_key}/#{related.id}"
        end
      end
    end

    def collect_counter_keys
      keys_to_delete << "#{record.class.model_name.cache_key}/count/*"
    end

    def delete_keys
      keys_to_delete.each do |key|
        if key.include?('*')
          Rails.cache.delete_matched(key)
        else
          Rails.cache.delete(key)
        end
      end
    end
  end
end
```

---

## 10. Testing Caching

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'Caching', type: :request do
  describe 'GET /api/v1/posts/:id' do
    let(:post) { create(:post) }

    it 'caches the response' do
      # First request - cache miss
      get "/api/v1/posts/#{post.id}"
      expect(response).to have_http_status(:ok)

      # Verify cache was written
      expect(Rails.cache.exist?("posts/#{post.id}")).to be true

      # Second request - cache hit (no DB query)
      expect {
        get "/api/v1/posts/#{post.id}"
      }.not_to make_database_queries

      expect(response).to have_http_status(:ok)
    end

    it 'invalidates cache on update' do
      # Warm cache
      get "/api/v1/posts/#{post.id}"

      # Update post
      post.update!(title: 'New Title')

      # Cache should be invalidated
      expect(Rails.cache.exist?("posts/#{post.id}")).to be false
    end
  end
end

RSpec.describe Post do
  describe '#cached_comments_count' do
    let(:post) { create(:post) }

    it 'caches the count' do
      create_list(:comment, 3, post: post)

      # First call - calculates and caches
      expect(post.cached_comments_count).to eq(3)

      # Add more comments
      create(:comment, post: post)

      # Still returns cached value
      expect(post.cached_comments_count).to eq(3)

      # After expiring cache
      post.expire_comments_cache
      expect(post.cached_comments_count).to eq(4)
    end
  end
end
```
