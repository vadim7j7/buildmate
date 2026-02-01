# Rails Agent System

This project uses a multi-agent architecture powered by Claude Code, specialised for
Ruby on Rails backends. A single main agent orchestrates work by delegating to
specialised sub-agents through the **Task** tool. Sub-agents never spawn their own
sub-agents; only the main agent delegates.

## Quick Start

Say **"Use PM: [task description]"** in any conversation to trigger the full
orchestration pipeline. The PM agent will break the task down, create a feature file,
and drive the pipeline to completion.

## Project Structure

```
app/
  controllers/        # RESTful controllers, concerns, strong params
  models/             # ActiveRecord models, associations, validations, scopes
  services/           # Service objects (namespaced under modules)
  presenters/         # Presenter objects (BasePresenter inheritance)
  jobs/               # Sidekiq background jobs (namespaced)
  mailers/            # ActionMailer classes
  views/              # ERB/Jbuilder/JSON views
config/
  routes.rb           # RESTful routing
  initializers/       # App configuration
db/
  migrate/            # Database migrations
  schema.rb           # Current schema state
lib/                  # Shared libraries, custom Rake tasks
spec/
  models/             # Model specs (associations, validations, scopes)
  requests/           # Request specs (controller integration tests)
  services/           # Service object specs
  presenters/         # Presenter specs
  jobs/               # Job specs
  factories/          # FactoryBot factories
  support/            # Shared spec helpers
```

## Key Commands

| Command                        | Purpose                              |
|--------------------------------|--------------------------------------|
| `bundle exec rspec`            | Run the full test suite              |
| `bundle exec rspec spec/path`  | Run a specific spec file or dir      |
| `bundle exec rubocop`          | Lint all Ruby files                  |
| `bundle exec rubocop -A`       | Auto-fix lint violations             |
| `rails db:migrate`             | Run pending database migrations      |
| `rails db:rollback`            | Roll back the last migration         |
| `rails console`                | Open interactive Rails console       |
| `rails routes`                 | List all defined routes              |
| `bundle exec rails generate`   | Run Rails generators                 |

## Agent Pipeline

Every non-trivial task flows through the following stages:

```
Plan --> Implement --> Test --> Review --> Eval --> Security
```

| Stage      | Agent              | Purpose                                    |
|------------|--------------------|--------------------------------------------|
| Plan       | PM (orchestrator)  | Break task into sub-tasks, create feature  |
| Implement  | backend-developer  | Write production Rails code                |
| Test       | backend-tester     | Write and run RSpec tests                  |
| Review     | backend-reviewer   | Code review against Rails conventions      |
| Eval       | eval-agent         | Score against quality rubrics              |
| Security   | security-auditor   | OWASP scan, vulnerability check            |

## Code Patterns

### Service Pattern

Services are namespaced under modules and inherit from `ApplicationService`. They
accept keyword arguments and expose a single `call` method.

```ruby
# frozen_string_literal: true

module Users
  class SyncProfileService < ApplicationService
    def initialize(user:, provider:)
      @user = user
      @provider = provider
    end

    def call
      # implementation
    end
  end
end
```

### Presenter Pattern

Presenters inherit from `BasePresenter` and expose a `call` method that returns
a hash suitable for JSON serialization.

```ruby
# frozen_string_literal: true

class ProfilePresenter < BasePresenter
  def call
    {
      id:,
      name:,
      email:,
      created_at:
    }
  end
end
```

### Controller Pattern

Controllers are RESTful, use strong params, extract shared logic into concerns,
and use before_actions for authorization and resource loading.

```ruby
# frozen_string_literal: true

class ProfilesController < ApplicationController
  before_action :authenticate_user!
  before_action :set_profile, only: %i[show update destroy]

  def index
    profiles = Profile.includes(:company, :tags).page(params[:page])
    render json: ProfilePresenter.new(profiles).call
  end

  private

  def set_profile
    @profile = Profile.find(params[:id])
  end

  def profile_params
    params.require(:profile).permit(:name, :email, :bio)
  end
end
```

### Model Pattern

Models declare associations, validations, scopes, and callbacks in a consistent
order. Use `includes()` for N+1 prevention.

```ruby
# frozen_string_literal: true

class Profile < ApplicationRecord
  # Associations
  belongs_to :company
  has_many :experiences, dependent: :destroy
  has_many :tags, through: :profile_tags

  # Validations
  validates :name, presence: true
  validates :email, presence: true, uniqueness: true

  # Scopes
  scope :active, -> { where(active: true) }
  scope :recent, -> { order(created_at: :desc) }

  # Callbacks
  after_create :send_welcome_email
end
```

### Job Pattern

Jobs use Sidekiq, are namespaced under modules, and configure retry behaviour.

```ruby
# frozen_string_literal: true

module Sync
  class AirtableImportJob < ApplicationJob
    queue_as :default
    sidekiq_options retry: 3

    def perform(import_id)
      import = Import.find(import_id)
      Sync::AirtableImportService.new(import:).call
    end
  end
end
```

## Ruby Style Rules

- **frozen_string_literal: true** on all files
- **Single quotes** for strings, double quotes only for interpolation
- **Hash shorthand**: `{ id:, name: }` instead of `{ id: id, name: name }`
- **Guard clauses** over nested conditionals
- **YARD documentation** on all public methods
- **Naming**: snake_case for methods/variables, CamelCase for classes/modules
- Method organization: public, then private, sorted by usage order
- Prefer `includes()` and `preload()` over lazy loading to prevent N+1 queries

## Quality Gates

Before the review stage, the following gates **must** pass:

| Gate     | Command               | Requirement   |
|----------|-----------------------|---------------|
| Lint     | `bundle exec rubocop` | Zero offenses |
| Tests    | `bundle exec rspec`   | All passing   |
| Eval     | Eval agent score      | >= 0.7        |

If any gate fails, the implementing agent must fix the issues before proceeding.

## Feature Tracking

Features are tracked as markdown files in `.claude/context/features/`.

```bash
# Convention: YYYYMMDD-short-slug.md
touch .claude/context/features/20260201-user-sync.md
```

## Available Slash Commands

| Command           | Description                                          |
|-------------------|------------------------------------------------------|
| `/test`           | Run RSpec tests via backend-tester agent             |
| `/review`         | Code review via backend-reviewer agent               |
| `/db-migrate`     | Create and run database migrations safely            |
| `/new-service`    | Generate a namespaced service object                 |
| `/new-controller` | Generate a RESTful controller                        |
| `/new-model`      | Generate an ActiveRecord model                       |
| `/new-job`        | Generate a Sidekiq background job                    |
| `/new-presenter`  | Generate a presenter object                          |
| `/new-migration`  | Generate a database migration                        |
| `/new-spec`       | Generate an RSpec test file                          |

## Delegation Rules

1. **Only the main agent delegates.** Sub-agents receive a task, execute it,
   and return results. They never call the Task tool themselves.
2. **One responsibility per agent.** Each sub-agent owns a single concern
   (implementing, testing, reviewing).
3. **Context flows forward.** Each stage writes its output to
   `.agent-pipeline/<stage>.md` so the next stage can read it.
4. **Failures stop the pipeline.** If a stage fails, the pipeline halts and
   the main agent reports the failure with actionable details.
