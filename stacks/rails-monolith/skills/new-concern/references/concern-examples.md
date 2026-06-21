# Rails Concern Examples

Reference examples for generating concerns.

## Model Concern: Sluggable

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
    def sluggable_attribute(attribute)
      self.slug_source_attribute = attribute
    end

    def find_by_slug!(slug)
      find_by!(slug: slug)
    end
  end

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

## Model Concern: SoftDeletable

```ruby
# frozen_string_literal: true

# Provides soft delete functionality using a deleted_at timestamp.
#
# @example Include in a model
#   class Comment < ApplicationRecord
#     include SoftDeletable
#   end
#
module SoftDeletable
  extend ActiveSupport::Concern

  included do
    scope :kept, -> { where(deleted_at: nil) }
    scope :discarded, -> { where.not(deleted_at: nil) }

    default_scope { kept }
  end

  class_methods do
    def with_discarded
      unscope(where: :deleted_at)
    end
  end

  def discard
    update(deleted_at: Time.current)
  end

  def discard!
    update!(deleted_at: Time.current)
  end

  def undiscard
    update(deleted_at: nil)
  end

  def discarded?
    deleted_at.present?
  end

  def kept?
    deleted_at.nil?
  end
end
```

## Model Concern: Searchable

```ruby
# frozen_string_literal: true

# Provides full-text search using PostgreSQL.
#
# @example Include in a model
#   class Article < ApplicationRecord
#     include Searchable
#     searchable_columns :title, :body, :author_name
#   end
#
module Searchable
  extend ActiveSupport::Concern

  included do
    class_attribute :search_columns, default: []

    scope :search, ->(query) {
      return all if query.blank?

      where(search_condition(query))
    }
  end

  class_methods do
    def searchable_columns(*columns)
      self.search_columns = columns.map(&:to_s)
    end

    private

    def search_condition(query)
      terms = query.split(/\s+/).map { |term| "%#{sanitize_sql_like(term)}%" }

      conditions = search_columns.flat_map do |column|
        terms.map { |term| arel_table[column].matches(term) }
      end

      conditions.reduce(:or)
    end
  end
end
```

## Controller Concern: Authenticatable

```ruby
# frozen_string_literal: true

# Provides authentication helpers for controllers.
#
# @example Include in a controller
#   class ApplicationController < ActionController::Base
#     include Authenticatable
#   end
#
module Authenticatable
  extend ActiveSupport::Concern

  included do
    helper_method :current_user, :user_signed_in?

    before_action :set_current_user
  end

  private

  def current_user
    @current_user
  end

  def user_signed_in?
    current_user.present?
  end

  def authenticate_user!
    return if user_signed_in?

    respond_to do |format|
      format.html { redirect_to login_path, alert: 'Please sign in to continue.' }
      format.json { render json: { error: 'Unauthorized' }, status: :unauthorized }
    end
  end

  def set_current_user
    @current_user = User.find_by(id: session[:user_id]) if session[:user_id]
  end
end
```

## Controller Concern: Paginatable

```ruby
# frozen_string_literal: true

# Provides pagination helpers for controllers.
#
# @example Include in a controller
#   class PostsController < ApplicationController
#     include Paginatable
#
#     def index
#       @posts = paginate(Post.all)
#     end
#   end
#
module Paginatable
  extend ActiveSupport::Concern

  DEFAULT_PER_PAGE = 25
  MAX_PER_PAGE = 100

  private

  def paginate(relation)
    relation
      .page(page_param)
      .per(per_page_param)
  end

  def page_param
    params.fetch(:page, 1).to_i.clamp(1, Float::INFINITY)
  end

  def per_page_param
    params.fetch(:per_page, DEFAULT_PER_PAGE).to_i.clamp(1, MAX_PER_PAGE)
  end

  def pagination_meta(collection)
    {
      current_page: collection.current_page,
      total_pages: collection.total_pages,
      total_count: collection.total_count,
      per_page: collection.limit_value
    }
  end
end
```

## Spec Example: Sluggable

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Sluggable do
  # Create a test class that includes the concern
  let(:test_class) do
    Class.new(ApplicationRecord) do
      self.table_name = 'posts'
      include Sluggable
      sluggable_attribute :title
    end
  end

  let(:instance) { test_class.new(title: 'Hello World') }

  describe '#generate_slug' do
    it 'generates a slug from the source attribute' do
      instance.valid?
      expect(instance.slug).to eq('hello-world')
    end

    it 'does not overwrite existing slugs' do
      instance.slug = 'custom-slug'
      instance.valid?
      expect(instance.slug).to eq('custom-slug')
    end
  end

  describe '#to_param' do
    it 'returns the slug' do
      instance.slug = 'my-slug'
      expect(instance.to_param).to eq('my-slug')
    end
  end

  describe '.find_by_slug!' do
    it 'finds by slug' do
      instance.save!
      expect(test_class.find_by_slug!('hello-world')).to eq(instance)
    end

    it 'raises RecordNotFound for missing slug' do
      expect { test_class.find_by_slug!('nonexistent') }
        .to raise_error(ActiveRecord::RecordNotFound)
    end
  end
end
```
