# Serializer Examples

Reference examples for generating Alba and JSON:API serializers.

## Alba: Basic Serializer

```ruby
# frozen_string_literal: true

# Serializes User for API responses.
#
# @example Basic usage
#   UserSerializer.new(user).serialize
#
# @example Collection
#   UserSerializer.new(users).serialize
#
class UserSerializer
  include Alba::Resource

  attributes :id, :email, :name, :created_at

  attribute :avatar_url do |user|
    user.avatar.attached? ? url_for(user.avatar) : nil
  end
end
```

## Alba: With Associations

```ruby
# frozen_string_literal: true

# Serializes Post with author and comments.
#
class PostSerializer
  include Alba::Resource

  attributes :id, :title, :body, :published_at, :created_at, :updated_at

  # Computed attributes
  attribute :excerpt do |post|
    post.body.truncate(200)
  end

  attribute :reading_time do |post|
    words = post.body.split.size
    (words / 200.0).ceil # minutes at 200 wpm
  end

  attribute :published do |post|
    post.published_at.present?
  end

  # Associations
  one :author, resource: UserSerializer
  many :comments, resource: CommentSerializer
  many :tags, resource: TagSerializer

  # Conditional association
  one :featured_image, resource: ImageSerializer, if: proc { |post| post.featured_image.attached? }
end
```

## Alba: Conditional Attributes

```ruby
# frozen_string_literal: true

# Serializes Order with conditional attributes based on context.
#
class OrderSerializer
  include Alba::Resource

  attributes :id, :status, :total_cents, :created_at

  # Only include for admins
  attribute :internal_notes, if: proc { |order, params|
    params[:current_user]&.admin?
  }

  # Only include if present
  attribute :discount_code, if: proc { |order| order.discount_code.present? }

  # Format currency
  attribute :total do |order|
    Money.new(order.total_cents).format
  end

  many :line_items, resource: LineItemSerializer
  one :shipping_address, resource: AddressSerializer
end
```

## Alba: Nested Serializer

```ruby
# frozen_string_literal: true

# Serializes Comment with nested author.
#
class CommentSerializer
  include Alba::Resource

  attributes :id, :body, :created_at

  # Inline nested serializer
  one :author do
    attributes :id, :name, :avatar_url
  end

  many :replies, resource: CommentSerializer
end
```

## JSON:API: Basic Serializer

```ruby
# frozen_string_literal: true

# Serializes User for JSON:API responses.
#
class UserSerializer
  include JSONAPI::Serializer

  set_type :users
  set_id :id

  attributes :email, :name, :created_at

  attribute :avatar_url do |user|
    user.avatar.attached? ? Rails.application.routes.url_helpers.url_for(user.avatar) : nil
  end

  link :self do |user|
    Rails.application.routes.url_helpers.api_v1_user_url(user)
  end
end
```

## JSON:API: With Relationships

```ruby
# frozen_string_literal: true

# Serializes Post for JSON:API responses with relationships.
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
  has_many :tags, serializer: TagSerializer

  link :self do |post|
    Rails.application.routes.url_helpers.api_v1_post_url(post)
  end

  meta do |post|
    { comment_count: post.comments.count }
  end
end
```

## JSON:API: Sparse Fieldsets

```ruby
# frozen_string_literal: true

# Serializes Article with sparse fieldset support.
#
class ArticleSerializer
  include JSONAPI::Serializer

  set_type :articles

  # All available attributes
  attributes :title, :body, :summary, :author_name,
             :published_at, :created_at, :updated_at

  belongs_to :category
  has_many :tags

  # Usage with sparse fieldsets:
  # ArticleSerializer.new(article, fields: { articles: [:title, :summary] })
end
```

## Presenter Pattern (Alternative)

```ruby
# frozen_string_literal: true

# Presents User for API responses.
# Use when you need more control than serializers provide.
#
class Users::ShowPresenter
  def initialize(user, current_user: nil)
    @user = user
    @current_user = current_user
  end

  def as_json
    {
      id: @user.id,
      email: @user.email,
      name: @user.name,
      avatar_url: avatar_url,
      created_at: @user.created_at.iso8601,
      **admin_fields
    }
  end

  private

  attr_reader :user, :current_user

  def avatar_url
    return nil unless @user.avatar.attached?

    Rails.application.routes.url_helpers.url_for(@user.avatar)
  end

  def admin_fields
    return {} unless @current_user&.admin?

    {
      admin_notes: @user.admin_notes,
      last_login_at: @user.last_login_at&.iso8601
    }
  end
end
```

## Spec: Alba Serializer

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe PostSerializer do
  subject(:serialized) { described_class.new(post).serialize }

  let(:author) { create(:user, name: 'Jane Doe') }
  let(:post) do
    create(:post,
           title: 'Test Post',
           body: 'A' * 500, # 500 characters
           author: author,
           published_at: Time.current)
  end

  describe 'attributes' do
    it 'includes basic attributes' do
      expect(serialized).to include(
        'id' => post.id,
        'title' => 'Test Post',
        'published_at' => post.published_at.as_json
      )
    end

    it 'includes excerpt (truncated body)' do
      expect(serialized['excerpt'].length).to be <= 203 # 200 + "..."
    end

    it 'includes reading_time calculation' do
      # 500 chars / ~5 chars per word = ~100 words
      # 100 words / 200 wpm = 0.5, ceil = 1
      expect(serialized['reading_time']).to eq(1)
    end

    it 'includes published boolean' do
      expect(serialized['published']).to be true
    end
  end

  describe 'associations' do
    it 'includes author' do
      expect(serialized['author']).to include(
        'id' => author.id,
        'name' => 'Jane Doe'
      )
    end

    context 'with comments' do
      let!(:comment) { create(:comment, post: post) }

      it 'includes comments' do
        expect(serialized['comments']).to be_an(Array)
        expect(serialized['comments'].first).to include('id' => comment.id)
      end
    end
  end

  context 'with unpublished post' do
    let(:post) { create(:post, published_at: nil) }

    it 'sets published to false' do
      expect(serialized['published']).to be false
    end
  end
end
```

## Spec: JSON:API Serializer

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe PostSerializer do
  subject(:serialized) { described_class.new(post).serializable_hash }

  let(:post) { create(:post) }

  describe 'type' do
    it 'sets correct type' do
      expect(serialized[:data][:type]).to eq(:posts)
    end
  end

  describe 'attributes' do
    let(:attributes) { serialized[:data][:attributes] }

    it 'includes expected attributes' do
      expect(attributes.keys).to include(
        :title, :body, :excerpt, :reading_time, :published_at
      )
    end
  end

  describe 'relationships' do
    let(:relationships) { serialized[:data][:relationships] }

    it 'includes author relationship' do
      expect(relationships).to have_key(:author)
    end

    it 'includes comments relationship' do
      expect(relationships).to have_key(:comments)
    end
  end

  describe 'links' do
    let(:links) { serialized[:data][:links] }

    it 'includes self link' do
      expect(links[:self]).to include("/api/v1/posts/#{post.id}")
    end
  end
end
```

## Controller Usage

```ruby
# frozen_string_literal: true

module Api
  module V1
    class PostsController < ApplicationController
      def index
        posts = Post.published.includes(:author, :tags).page(params[:page])

        render json: PostSerializer.new(posts).serialize
      end

      def show
        post = Post.includes(:author, :comments, :tags).find(params[:id])

        render json: PostSerializer.new(post).serialize
      end
    end
  end
end
```
