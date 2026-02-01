# Full-Stack Agent System (Rails + React/Next.js)

This project uses a multi-agent architecture powered by Claude Code, designed for
full-stack applications with a Ruby on Rails backend and a React + Next.js frontend.
A single main agent orchestrates work by delegating to specialised sub-agents through
the **Task** tool. Sub-agents never spawn their own sub-agents; only the main agent
delegates.

## Quick Start

Say **"Use PM: [task description]"** in any conversation to trigger the full
orchestration pipeline. The PM agent will break the task down, create a feature file,
and drive the pipeline to completion across both backend and frontend.

## Workspace Structure

```
backend/                     # Rails API application
  app/
    controllers/             # RESTful controllers, concerns, strong params
    models/                  # ActiveRecord models, associations, validations, scopes
    services/                # Service objects (namespaced under modules)
    presenters/              # Presenter objects (BasePresenter inheritance)
    jobs/                    # Sidekiq background jobs (namespaced)
    mailers/                 # ActionMailer classes
    views/                   # ERB/Jbuilder/JSON views
  config/
    routes.rb                # RESTful routing
    initializers/            # App configuration
  db/
    migrate/                 # Database migrations
    schema.rb                # Current schema state
  lib/                       # Shared libraries, custom Rake tasks
  spec/
    models/                  # Model specs
    requests/                # Request specs
    services/                # Service object specs
    presenters/              # Presenter specs
    jobs/                    # Job specs
    factories/               # FactoryBot factories
    support/                 # Shared spec helpers

frontend/                    # Next.js application
  src/
    app/                     # Next.js App Router pages and layouts
      (auth)/                # Route groups for authentication pages
      api/                   # API routes (route handlers)
      layout.tsx             # Root layout
      page.tsx               # Root page
    components/              # Presentational (UI) components
    containers/              # Data-fetching + state management wrappers
    services/                # API service modules (HTTP client wrappers)
    contexts/                # React Context providers and hooks
    hooks/                   # Custom React hooks
    utils/                   # Utility functions
    types/                   # Shared TypeScript type definitions
    styles/                  # Global styles and theme configuration
  e2e/                       # Playwright E2E tests
```

## Tech Stacks

### Backend (Rails)

| Technology | Purpose |
|---|---|
| Ruby on Rails 7+ | Web framework |
| PostgreSQL | Primary database |
| Redis | Caching, Sidekiq backend |
| Sidekiq | Background job processing |
| RSpec | Testing framework |
| FactoryBot | Test data factories |
| Rubocop | Ruby linter |

### Frontend (React + Next.js)

| Technology | Purpose |
|---|---|
| Next.js 14+ (App Router) | React framework |
| TypeScript (strict mode) | Language |
| Mantine v7+ | UI component library |
| Jest + React Testing Library | Unit/integration testing |
| Playwright | End-to-end testing |
| ESLint | Linter |

## Key Commands

### Backend Commands

| Command | Purpose |
|---|---|
| `cd backend && bundle exec rspec` | Run the full backend test suite |
| `cd backend && bundle exec rspec spec/path` | Run a specific spec file or dir |
| `cd backend && bundle exec rubocop` | Lint all Ruby files |
| `cd backend && bundle exec rubocop -A` | Auto-fix lint violations |
| `cd backend && rails db:migrate` | Run pending database migrations |
| `cd backend && rails db:rollback` | Roll back the last migration |
| `cd backend && rails routes` | List all defined routes |

### Frontend Commands

| Command | Purpose |
|---|---|
| `cd frontend && npm run lint` | Lint frontend code |
| `cd frontend && npx tsc --noEmit` | TypeScript type checking |
| `cd frontend && npm test` | Run Jest test suite |
| `cd frontend && npx jest path/to/file` | Run a specific test file |
| `cd frontend && npm run build` | Production build |
| `cd frontend && npm run dev` | Start dev server |
| `cd frontend && npx prettier --write "src/**/*.{ts,tsx}"` | Format code |

## Agent Pipeline

Every non-trivial full-stack task flows through the following stages:

```
Plan --> Implement (BE + FE in parallel) --> Test (BE + FE in parallel) --> Review (BE + FE in parallel) --> Eval --> Security
```

| Stage | Agent(s) | Purpose |
|---|---|---|
| Plan | PM (orchestrator) | Break task into backend + frontend sub-tasks |
| Implement | backend-developer, frontend-developer | Write production code (parallel) |
| Test | backend-tester, frontend-tester | Write and run tests (parallel) |
| Review | backend-reviewer, frontend-reviewer | Code review against conventions (parallel) |
| Eval | eval-agent | Score against quality rubrics |
| Security | security-auditor | OWASP scan, vulnerability check |

## Code Patterns

### Backend: Service Pattern

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

### Backend: Controller Pattern

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

### Frontend: Container Pattern

```typescript
'use client';

import { useState, useEffect } from 'react';

export function ProjectListContainer() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchProjectsApi();
        setProjects(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load projects');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <LoadingOverlay visible />;
  if (error) return <Alert color="red">{error}</Alert>;

  return <ProjectList projects={projects} />;
}
```

### Frontend: API Service Pattern

```typescript
// frontend/src/services/projects.ts
export const fetchProjectsApi = () => request<Project[]>('/api/projects');
export const createProjectApi = (data: CreateProjectPayload) =>
  request<Project>('/api/projects', { method: 'POST', body: JSON.stringify(data) });
```

## Style Rules

### Ruby (Backend)

- **frozen_string_literal: true** on all files
- **Single quotes** for strings, double quotes only for interpolation
- **Hash shorthand**: `{ id:, name: }` instead of `{ id: id, name: name }`
- **Guard clauses** over nested conditionals
- **YARD documentation** on all public methods
- **Naming**: snake_case for methods/variables, CamelCase for classes/modules
- Prefer `includes()` and `preload()` over lazy loading to prevent N+1 queries

### TypeScript (Frontend)

- **Server Components by default** -- add `'use client'` only when needed
- **`type` for props** -- not `interface`
- **No `any` types** -- use `unknown` with type guards
- **Mantine UI components** -- no raw HTML for standard elements
- **`@/` imports** -- absolute imports mapped to `src/`
- **Named exports** for components, services, and hooks
- **IIFE async pattern** inside `useEffect` for data fetching

## Quality Gates

Before the review stage, the following gates **must** pass for both stacks:

### Backend Gates

| Gate | Command | Requirement |
|---|---|---|
| Lint | `cd backend && bundle exec rubocop` | Zero offenses |
| Tests | `cd backend && bundle exec rspec` | All passing |

### Frontend Gates

| Gate | Command | Requirement |
|---|---|---|
| TypeScript | `cd frontend && npx tsc --noEmit` | Zero errors |
| Lint | `cd frontend && npm run lint` | Zero errors |
| Tests | `cd frontend && npm test` | All passing |

### Shared Gates

| Gate | Requirement |
|---|---|
| Eval score | >= 0.7 |
| Security audit | No critical vulnerabilities |

If any gate fails, the implementing agent must fix the issues before proceeding.

## Feature Tracking

Features are tracked as markdown files in `.claude/context/features/`.

```bash
# Convention: YYYYMMDD-short-slug.md
touch .claude/context/features/20260201-user-dashboard.md
```

## Available Slash Commands

### Backend Commands

| Command | Description |
|---|---|
| `/test` | Run RSpec tests via backend-tester agent |
| `/review` | Code review via backend-reviewer agent |
| `/db-migrate` | Create and run database migrations safely |
| `/new-service` | Generate a namespaced service object |
| `/new-controller` | Generate a RESTful controller |
| `/new-model` | Generate an ActiveRecord model |
| `/new-job` | Generate a Sidekiq background job |
| `/new-presenter` | Generate a presenter object |
| `/new-migration` | Generate a database migration |
| `/new-spec` | Generate an RSpec test file |

### Frontend Commands

| Command | Description |
|---|---|
| `/fe-test` | Run Jest + Playwright tests via frontend-tester |
| `/fe-review` | Code review via frontend-reviewer agent |
| `/new-component` | Generate a React component |
| `/new-page` | Generate a Next.js page |
| `/new-container` | Generate a container component |
| `/new-form` | Generate a Mantine form component |
| `/new-api-service` | Generate an API service module |
| `/new-context` | Generate a React Context provider |

### Full-Stack Commands

| Command | Description |
|---|---|
| `/pm` | Run the full PM orchestration pipeline |
| `/fullstack-test` | Run both backend and frontend test suites |
| `/fullstack-review` | Code review across both stacks |

## Delegation Rules

1. **Only the main agent delegates.** Sub-agents receive a task, execute it,
   and return results. They never call the Task tool themselves.
2. **One responsibility per agent.** Each sub-agent owns a single concern
   (implementing, testing, reviewing) within a single stack (backend or frontend).
3. **Parallel execution.** Backend and frontend work is delegated in parallel
   when there are no cross-stack dependencies.
4. **Context flows forward.** Each stage writes its output to
   `.agent-pipeline/<stage>.md` so the next stage can read it.
5. **Failures stop the pipeline.** If a stage fails, the pipeline halts and
   the main agent reports the failure with actionable details.
6. **API contracts bridge stacks.** When backend and frontend work depends on
   shared API contracts, define the API shape first before parallel implementation.
