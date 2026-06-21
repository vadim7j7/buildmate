# Pundit Policy Examples

Reference examples for generating authorization policies.

## Basic ApplicationPolicy

```ruby
# frozen_string_literal: true

# Base policy that all other policies inherit from.
# Provides default authorization behavior.
#
class ApplicationPolicy
  attr_reader :user, :record

  def initialize(user, record)
    @user = user
    @record = record
  end

  def index?
    false
  end

  def show?
    false
  end

  def create?
    false
  end

  def new?
    create?
  end

  def update?
    false
  end

  def edit?
    update?
  end

  def destroy?
    false
  end

  # Base scope for filtering records
  class Scope
    def initialize(user, scope)
      @user = user
      @scope = scope
    end

    def resolve
      raise NotImplementedError, "You must define #resolve in #{self.class}"
    end

    private

    attr_reader :user, :scope
  end
end
```

## Resource Policy: PostPolicy

```ruby
# frozen_string_literal: true

# Authorization policy for Post resources.
#
# @example Check authorization
#   authorize @post, :update?
#   policy_scope(Post)
#
class PostPolicy < ApplicationPolicy
  def index?
    true
  end

  def show?
    record.published? || owner? || admin?
  end

  def create?
    user.present?
  end

  def update?
    owner? || admin?
  end

  def destroy?
    owner? || admin?
  end

  def publish?
    owner? || admin?
  end

  def unpublish?
    owner? || admin?
  end

  private

  def owner?
    record.user_id == user&.id
  end

  def admin?
    user&.admin?
  end

  class Scope < ApplicationPolicy::Scope
    def resolve
      if user&.admin?
        scope.all
      elsif user
        scope.where(published: true).or(scope.where(user: user))
      else
        scope.where(published: true)
      end
    end
  end
end
```

## Nested Resource Policy: CommentPolicy

```ruby
# frozen_string_literal: true

# Authorization policy for Comment resources.
# Comments belong to posts, so we check both comment and post ownership.
#
class CommentPolicy < ApplicationPolicy
  def index?
    true
  end

  def show?
    post_visible?
  end

  def create?
    user.present? && post_visible?
  end

  def update?
    comment_owner?
  end

  def destroy?
    comment_owner? || post_owner? || admin?
  end

  private

  def comment_owner?
    record.user_id == user&.id
  end

  def post_owner?
    record.post.user_id == user&.id
  end

  def post_visible?
    record.post.published? || post_owner? || admin?
  end

  def admin?
    user&.admin?
  end

  class Scope < ApplicationPolicy::Scope
    def resolve
      scope.joins(:post).where(posts: { published: true })
           .or(scope.joins(:post).where(posts: { user_id: user&.id }))
    end
  end
end
```

## Admin Namespace Policy

```ruby
# frozen_string_literal: true

# Policy for admin-only resources.
#
class Admin::SettingPolicy < ApplicationPolicy
  def index?
    admin?
  end

  def show?
    admin?
  end

  def create?
    admin?
  end

  def update?
    admin?
  end

  def destroy?
    super_admin?
  end

  private

  def admin?
    user&.admin? || user&.super_admin?
  end

  def super_admin?
    user&.super_admin?
  end

  class Scope < ApplicationPolicy::Scope
    def resolve
      return scope.none unless user&.admin?

      scope.all
    end
  end
end
```

## Team-Based Policy: ProjectPolicy

```ruby
# frozen_string_literal: true

# Authorization policy for Project resources.
# Projects belong to teams, and permissions are role-based.
#
class ProjectPolicy < ApplicationPolicy
  def index?
    true
  end

  def show?
    team_member? || record.public?
  end

  def create?
    team_admin?
  end

  def update?
    project_maintainer?
  end

  def destroy?
    team_admin?
  end

  def archive?
    project_maintainer?
  end

  private

  def team
    record.team
  end

  def membership
    @membership ||= team.memberships.find_by(user: user)
  end

  def team_member?
    membership.present?
  end

  def team_admin?
    membership&.role.in?(%w[admin owner])
  end

  def project_maintainer?
    team_admin? || record.maintainers.include?(user)
  end

  class Scope < ApplicationPolicy::Scope
    def resolve
      scope.left_joins(team: :memberships)
           .where(memberships: { user_id: user.id })
           .or(scope.where(public: true))
           .distinct
    end
  end
end
```

## Spec Example: PostPolicy

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe PostPolicy do
  subject { described_class }

  let(:admin) { create(:user, :admin) }
  let(:author) { create(:user) }
  let(:other_user) { create(:user) }
  let(:guest) { nil }

  let(:published_post) { create(:post, user: author, published: true) }
  let(:draft_post) { create(:post, user: author, published: false) }

  describe 'index?' do
    permissions(:index?) do
      it 'allows everyone' do
        expect(subject).to permit(guest, Post)
        expect(subject).to permit(other_user, Post)
        expect(subject).to permit(admin, Post)
      end
    end
  end

  describe 'show?' do
    permissions(:show?) do
      context 'with published post' do
        it 'allows everyone' do
          expect(subject).to permit(guest, published_post)
          expect(subject).to permit(other_user, published_post)
        end
      end

      context 'with draft post' do
        it 'denies guests and other users' do
          expect(subject).not_to permit(guest, draft_post)
          expect(subject).not_to permit(other_user, draft_post)
        end

        it 'allows author and admin' do
          expect(subject).to permit(author, draft_post)
          expect(subject).to permit(admin, draft_post)
        end
      end
    end
  end

  describe 'create?' do
    permissions(:create?) do
      it 'denies guests' do
        expect(subject).not_to permit(guest, Post)
      end

      it 'allows authenticated users' do
        expect(subject).to permit(other_user, Post)
      end
    end
  end

  describe 'update?' do
    permissions(:update?) do
      it 'denies non-owners' do
        expect(subject).not_to permit(guest, published_post)
        expect(subject).not_to permit(other_user, published_post)
      end

      it 'allows author' do
        expect(subject).to permit(author, published_post)
      end

      it 'allows admin' do
        expect(subject).to permit(admin, published_post)
      end
    end
  end

  describe 'destroy?' do
    permissions(:destroy?) do
      it 'denies non-owners' do
        expect(subject).not_to permit(guest, published_post)
        expect(subject).not_to permit(other_user, published_post)
      end

      it 'allows author' do
        expect(subject).to permit(author, published_post)
      end

      it 'allows admin' do
        expect(subject).to permit(admin, published_post)
      end
    end
  end

  describe 'Scope' do
    let!(:published) { create(:post, published: true) }
    let!(:own_draft) { create(:post, user: author, published: false) }
    let!(:other_draft) { create(:post, user: other_user, published: false) }

    describe '#resolve' do
      context 'as admin' do
        it 'returns all posts' do
          scope = described_class::Scope.new(admin, Post).resolve
          expect(scope).to include(published, own_draft, other_draft)
        end
      end

      context 'as author' do
        it 'returns published posts and own drafts' do
          scope = described_class::Scope.new(author, Post).resolve
          expect(scope).to include(published, own_draft)
          expect(scope).not_to include(other_draft)
        end
      end

      context 'as guest' do
        it 'returns only published posts' do
          scope = described_class::Scope.new(nil, Post).resolve
          expect(scope).to include(published)
          expect(scope).not_to include(own_draft, other_draft)
        end
      end
    end
  end
end
```
