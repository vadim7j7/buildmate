---
name: new-policy
description: Generate a Pundit authorization policy with spec file
---

# /new-policy

## What This Does

Generates a Pundit authorization policy for a resource, defining who can perform
which actions. Also generates the corresponding RSpec spec file with
comprehensive authorization tests.

## Usage

```
/new-policy Post                  # Creates PostPolicy
/new-policy Project               # Creates ProjectPolicy
/new-policy Admin::Setting        # Creates Admin::SettingPolicy
```

## How It Works

1. **Read reference patterns.** Load policy patterns from:
   - `skills/new-policy/references/policy-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-ruby.md`

2. **Determine policy name.** Parse the argument to determine:
   - Class name (e.g., `PostPolicy`)
   - File path (e.g., `app/policies/post_policy.rb`)
   - Associated model (e.g., `Post`)

3. **Analyze the model.** Read the model to understand:
   - Associations (especially `belongs_to :user` or similar)
   - Any status or role attributes
   - Existing scopes that might inform policy scopes

4. **Generate the policy file.** Create the policy with:
   - `frozen_string_literal: true`
   - `ApplicationPolicy` inheritance
   - Standard CRUD methods: `index?`, `show?`, `create?`, `update?`, `destroy?`
   - Scope class for filtering collections
   - YARD documentation

5. **Generate the spec file.** Create the spec with:
   - Policy spec using `pundit-matchers` or direct testing
   - Context blocks for different user roles/states
   - Tests for each policy method
   - Scope tests

6. **Run quality checks.**

   ```bash
   bundle exec rubocop -A app/policies/<path>.rb spec/policies/<path>_spec.rb
   bundle exec rspec spec/policies/<path>_spec.rb
   ```

7. **Report results.** Show the generated files and test results.

## Generated Files

```
app/policies/<resource>_policy.rb
spec/policies/<resource>_policy_spec.rb
```

## Example Output

For `/new-policy Post`:

**Policy:** `app/policies/post_policy.rb`
```ruby
# frozen_string_literal: true

# Authorization policy for Post resources.
#
# @example Check if user can update a post
#   Pundit.authorize(current_user, post, :update?)
#
class PostPolicy < ApplicationPolicy
  # Anyone can view the list of posts.
  def index?
    true
  end

  # Anyone can view a published post; only author can view drafts.
  def show?
    record.published? || owner?
  end

  # Authenticated users can create posts.
  def create?
    user.present?
  end

  # Only the author can update their posts.
  def update?
    owner?
  end

  # Only the author or admins can delete posts.
  def destroy?
    owner? || user&.admin?
  end

  private

  def owner?
    record.user_id == user&.id
  end

  # Scope for filtering post collections.
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

**Spec:** `spec/policies/post_policy_spec.rb`

## Rules

- Inherit from `ApplicationPolicy` (create if missing)
- Policy methods should return booleans
- Keep authorization logic in policies, not controllers
- Use descriptive helper methods like `owner?`, `member?`
- The `Scope` class must implement `resolve`
- Test all user roles and edge cases
- Document complex authorization rules
