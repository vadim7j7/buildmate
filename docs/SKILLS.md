# Skills

Skill descriptions, usage examples, and how to create custom skills.

---

## Table of Contents

- [Overview](#overview)
- [Shared Skills](#shared-skills)
- [Rails Skills](#rails-skills)
- [React + Next.js Skills](#react--nextjs-skills)
- [React Native Skills](#react-native-skills)
- [Delegation Skills](#delegation-skills)
- [Utility Skills](#utility-skills)
- [Code Generation Skills](#code-generation-skills)
- [Creating Custom Skills](#creating-custom-skills)

---

## Overview

Skills are slash commands that provide specialized capabilities in Claude Code. Each skill is a directory under `.claude/skills/` containing a `SKILL.md` file (the skill's instructions) and an optional `references/` subdirectory with supporting documentation and examples.

Skills are invoked by typing `/<skill-name>` followed by optional arguments in the Claude Code chat:

```
/test                          # Run tests
/new-service UserSync          # Generate a new Rails service
/review --staged               # Review staged changes
```

---

## Shared Skills

These skills are available in every stack. They provide cross-cutting capabilities for delegation, testing, review, evaluation, security, and documentation.

| Command | Description | Arguments |
|---------|-------------|-----------|
| `/delegate` | Smart delegation -- analyzes tasks for dependencies and routes to parallel or sequential execution | Comma-separated or quoted task descriptions |
| `/parallel` | Run multiple independent tasks concurrently in isolated git worktrees | Quoted task descriptions; `--max N` to limit concurrency |
| `/sequential` | Run tasks through a pipeline where each stage feeds context to the next | Stage names (`implement`, `test`, `review`, `eval`, `docs`); `--from <stage>` to resume |
| `/test` | Detect the project's test framework and delegate test execution to the stack's tester agent | Optional file path; `--coverage` for coverage reporting |
| `/review` | Identify changed files and delegate code review to the stack's reviewer agent | Optional file path; `--staged` for staged changes only |
| `/eval` | Run quality evaluation against scoring rubrics (5 dimensions, weighted formula) | Optional file path; `--dimension <name>` for a single dimension |
| `/security` | Run a security audit scanning for OWASP Top 10 vulnerabilities | Optional file path; `--full` for entire codebase |
| `/docs` | Generate or update documentation for changed files | Optional file path; `--update` for existing docs only |
| `/resume` | Load saved session context and show a detailed status summary | None |

---

## Rails Skills

These skills are specific to the Rails stack and provide code generation and Rails-specific workflows.

| Command | Description | Arguments |
|---------|-------------|-----------|
| `/new-service` | Generate a namespaced service object with spec file | Service name (e.g., `UserSync`, `BulkImport::Profiles`) |
| `/new-controller` | Generate a RESTful controller with strong params, before_actions, and presenter usage | Controller name (e.g., `Profiles`, `Api::V1::Users`) |
| `/new-model` | Generate an ActiveRecord model with associations, validations, scopes, and migration | Model name (e.g., `Profile`, `Transaction`) |
| `/new-job` | Generate a namespaced Sidekiq background job | Job name (e.g., `Sync::AirtableImport`) |
| `/new-presenter` | Generate a presenter object inheriting from BasePresenter | Presenter name (e.g., `ProfilePresenter`) |
| `/new-migration` | Generate a database migration | Migration description (e.g., `AddEmailToProfiles`) |
| `/new-spec` | Generate an RSpec test file matching the target file's type | Target file path or class name |
| `/test` | Run RSpec tests via the backend-tester agent (overrides shared) | Optional spec file path |
| `/review` | Code review via the backend-reviewer agent (overrides shared) | Optional file path; `--staged` |
| `/db-migrate` | Create and run database migrations safely | Migration description |

---

## React + Next.js Skills

These skills are specific to the React + Next.js stack.

| Command | Description | Arguments |
|---------|-------------|-----------|
| `/new-component` | Generate a React component with TypeScript props, Mantine UI, and a test file | Component name in PascalCase (e.g., `ProfileCard`) |
| `/new-page` | Generate a Next.js App Router page with metadata and container delegation | Page name and route path |
| `/new-container` | Generate a data-fetching container component with loading/error states | Container name (e.g., `ProjectListContainer`) |
| `/new-form` | Generate a form component using @mantine/form with validation and notifications | Form name (e.g., `CreateProjectForm`) |
| `/new-api-service` | Generate a typed API service module using the request wrapper | Service name and endpoint base path |
| `/new-context` | Generate a React Context with Provider, custom hook, and undefined safety | Context name (e.g., `AuthContext`) |
| `/component-gen` | Legacy component generation skill | Component specification |
| `/test` | Run Jest/Playwright tests via the frontend-tester agent (overrides shared) | Optional test file path |
| `/review` | Code review via the frontend-reviewer agent (overrides shared) | Optional file path; `--staged` |

---

## React Native Skills

These skills are specific to the React Native + Expo stack.

| Command | Description | Arguments |
|---------|-------------|-----------|
| `/new-screen` | Generate an expo-router screen with proper data loading, navigation, styling, i18n, and platform patterns | Screen name; `--modal`, `--auth`, `--type=list\|form\|detail` |
| `/new-rn-component` | Generate a React Native component with StyleSheet, theme constants, and platform handling | Component name in PascalCase |
| `/new-store` | Generate a Zustand store with typed state, actions, and selector hooks | Store name (e.g., `TransactionStore`) |
| `/new-query` | Generate a React Query hook with query key factory integration | Entity name (e.g., `Transactions`) |
| `/new-db-query` | Generate a Drizzle ORM query module for a database entity | Entity name |
| `/platform-check` | Verify platform-specific code for iOS and Android correctness | Optional file path |
| `/test` | Run Jest tests via the mobile-tester agent (overrides shared) | Optional test file path |
| `/review` | Code review via the mobile-code-reviewer agent (overrides shared) | Optional file path |

---

## Delegation Skills

These three shared skills manage how work is distributed across agents:

### /delegate -- Smart Delegation

Analyzes tasks for dependencies and automatically routes to the best execution strategy:

```
/delegate Implement user auth, add rate limiting, write API docs
/delegate "Build login page" "Build signup page" "Build dashboard"
```

How it works:
1. Parses input into individual tasks
2. Analyzes dependency types: data dependencies, order dependencies, resource dependencies
3. Builds a dependency graph (DAG)
4. Routes to `/parallel` (no dependencies), `/sequential` (all dependent), or hybrid (mix)
5. Reports the delegation plan before executing

Dependency detection heuristics:
- "test" tasks depend on "implement" tasks
- "docs" tasks depend on the feature they document
- Tasks modifying the same module are resource-dependent
- Ordering words ("then", "after", "once") indicate sequential dependency
- Tasks for different features or modules are typically independent

### /parallel -- Parallel Worktrees

Runs independent tasks concurrently in isolated git worktrees:

```
/parallel "Build login page" "Build signup page" "Build dashboard"
/parallel --max 3 "Task A" "Task B" "Task C" "Task D" "Task E"
```

Configuration:
- Maximum 5 concurrent worktrees (configurable with `--max`)
- 300-second per-task timeout
- Auto-merge of successful branches
- Automatic cleanup of worktrees after completion

### /sequential -- Pipeline Execution

Runs stages in order with context forwarding:

```
/sequential implement test review
/sequential implement test review eval docs
/sequential --from test    # Resume from a specific stage
```

Valid stages: `implement`, `test`, `review`, `eval`, `security`, `docs`

Each stage writes to `.agent-pipeline/<stage>.md` and the next stage reads all previous artifacts as context.

---

## Utility Skills

### /test -- Run Tests

Auto-detects the project's test framework and delegates to the stack's tester agent:

```
/test                          # Full test suite
/test path/to/file.test.tsx    # Specific file
/test --coverage               # With coverage
```

Supported frameworks: Jest, Vitest, Mocha, Playwright, RSpec, Minitest, pytest, cargo test, go test.

### /review -- Code Review

Identifies changed files and delegates to the stack's reviewer agent:

```
/review                        # All changed files vs base branch
/review path/to/file.ts        # Specific file
/review --staged               # Staged changes only
```

Returns findings categorized as blockers, warnings, or suggestions with a verdict of APPROVE or REQUEST_CHANGES.

### /eval -- Quality Evaluation

Scores code against five weighted dimensions:

```
/eval                          # All changed files
/eval path/to/file.ts          # Specific file
/eval --dimension security     # Single dimension
```

Scoring dimensions: Correctness (30%), Code Quality (15%), Security (25%), Performance (20%), Test Coverage (10%). See [EVALS.md](EVALS.md) for full details.

### /security -- Security Audit

Scans for OWASP Top 10 vulnerabilities:

```
/security                      # Changed files
/security path/to/file.ts      # Specific file
/security --full               # Entire codebase
```

Returns findings classified by severity (CRITICAL, HIGH, MEDIUM, LOW, INFO).

### /resume -- Session Resume

Loads saved context from a previous session and presents a structured status summary:

```
/resume
```

This skill is **read-only** — it never modifies files or changes state. It checks:

1. **Active work context** — `.claude/context/active-work.md` (auto-saved after each Claude response by the session-save hook)
2. **In-progress features** — Feature files in `.claude/context/features/` with status `in-progress`, `testing`, or `review`
3. **Git state** — Current branch, uncommitted changes, recent commits, stash list
4. **Pipeline state** — `.agent-pipeline/pipeline.json` if a pipeline was running
5. **Eval results** — Latest eval report in `.agent-eval-results/`

The output is a structured summary with suggested next steps based on the current state. Use this at the start of a session to quickly orient yourself, or whenever the session-load hook shows stale context.

**Note:** Session context is automatically saved and loaded by hooks in `settings.json`. The `/resume` command provides a more detailed assessment than the automatic session-load.

### /docs -- Documentation Generation

Generates or updates documentation for changed code:

```
/docs                          # All changed files
/docs path/to/file.ts          # Specific file
/docs --update                 # Update existing docs only
```

Produces inline documentation (JSDoc, docstrings, YARD), API docs, component docs, and module docs.

---

## Code Generation Skills

Code generation skills create new files following project patterns. Each skill reads reference examples from its `references/` directory and generates code that matches existing conventions.

### Rails Code Generation

#### /new-service

Generates a namespaced service object inheriting from `ApplicationService`:

```
/new-service UserSync                    # Creates Users::SyncService
/new-service BulkImport::Profiles        # Creates BulkImport::ProfilesService
/new-service Airtable::CompanySync       # Creates Airtable::CompanySyncService
```

Generates:
- `app/services/<namespace>/<service_name>.rb` -- Service class with keyword args, `call` method, guard clauses, YARD docs
- `spec/services/<namespace>/<service_name>_spec.rb` -- RSpec spec with happy path, edge cases, error handling

#### /new-controller

Generates a RESTful controller with standard CRUD actions:

```
/new-controller Profiles
/new-controller Api::V1::Users
```

Generates:
- Controller with `before_action`, strong params, presenter usage, pagination
- Request spec covering authentication, success, and error responses

#### /new-model

Generates an ActiveRecord model with associations, validations, and scopes:

```
/new-model Profile
/new-model Transaction
```

Generates:
- Model file with associations, validations, scopes, callbacks
- Database migration
- Model spec with association, validation, and scope tests
- FactoryBot factory

#### /new-job

Generates a namespaced Sidekiq background job:

```
/new-job Sync::AirtableImport
```

Generates:
- Job class with queue configuration, retry settings, error handling
- Job spec

#### /new-presenter

Generates a presenter object for API JSON serialization:

```
/new-presenter ProfilePresenter
```

Generates:
- Presenter class inheriting from `BasePresenter` with a `call` method
- Presenter spec

#### /new-migration

Generates a database migration:

```
/new-migration AddEmailToProfiles
/new-migration CreateTransactions
```

#### /new-spec

Generates an RSpec test file matching the target:

```
/new-spec app/services/users/sync_service.rb
/new-spec Profile
```

### React + Next.js Code Generation

#### /new-component

Generates a React component with TypeScript and Mantine UI:

```
/new-component ProfileCard
/new-component SearchBar
/new-component ConfirmDialog
```

Generates:
- `src/components/<Name>.tsx` -- Server or Client component with typed props, Mantine UI
- `src/components/<Name>.test.tsx` -- Jest + RTL test file

#### /new-page

Generates a Next.js App Router page:

```
/new-page Projects
/new-page ProjectDetail
```

Generates:
- `src/app/<route>/page.tsx` -- Page with metadata export, container delegation
- Layout file if needed

#### /new-container

Generates a data-fetching container component:

```
/new-container ProjectListContainer
```

Generates:
- `src/containers/<Name>.tsx` -- Client component with useEffect, loading/error/success states, API service calls

#### /new-form

Generates a form using @mantine/form:

```
/new-form CreateProjectForm
```

Generates:
- Form component with `useForm`, validation rules, `showNotification` feedback, async submission via IIFE

#### /new-api-service

Generates a typed API service module:

```
/new-api-service projects
```

Generates:
- `src/services/<name>.ts` -- Typed API functions using `request<T>()` wrapper (fetch, create, update, delete)

#### /new-context

Generates a React Context with Provider and custom hook:

```
/new-context AuthContext
```

Generates:
- `src/contexts/<Name>.tsx` -- Context with `createContext`, Provider component, `use<Name>` hook with undefined safety check

### React Native Code Generation

#### /new-screen

Generates an expo-router screen:

```
/new-screen Settings                      # Tab screen
/new-screen TransactionDetail             # Detail screen
/new-screen AddTransaction --modal        # Modal screen
/new-screen Login --auth                  # Auth screen
/new-screen BudgetList --type=list        # List screen with FlashList
/new-screen BudgetForm --type=form        # Form screen
/new-screen BudgetDetail --type=detail    # Detail screen with ScrollView
```

Generates:
- Screen file in the appropriate `app/` directory with navigation setup, data loading, i18n, platform handling

#### /new-rn-component

Generates a React Native component:

```
/new-rn-component TransactionCard
/new-rn-component AmountInput
```

Generates:
- Component with StyleSheet.create, theme constants from `@/constants`, platform-specific handling
- Test file

#### /new-store

Generates a Zustand store:

```
/new-store TransactionStore
```

Generates:
- Store with typed state, actions, reset function, and selector hooks for fine-grained subscriptions

#### /new-query

Generates a React Query hook:

```
/new-query Transactions
```

Generates:
- Query hook with `useQuery`, `useMutation`, query key factory integration, optimistic updates

#### /new-db-query

Generates a Drizzle ORM query module:

```
/new-db-query transactions
```

Generates:
- Query functions using Drizzle ORM (select, insert, update, delete) for the specified entity

---

## Creating Custom Skills

### Skill Directory Structure

Each skill is a directory under `.claude/skills/` containing at minimum a `SKILL.md` file:

```
.claude/skills/
  my-skill/
    SKILL.md              # Required: skill instructions
    references/           # Optional: supporting docs and examples
      example-1.md
      example-2.md
```

### SKILL.md Format

The `SKILL.md` file uses YAML frontmatter followed by Markdown instructions:

```markdown
---
name: my-skill
description: Brief description of what this skill does
---

# /my-skill

## What This Does

Describe what the skill does in one or two sentences.

## Usage

\```
/my-skill argument1
/my-skill argument1 --option
\```

## How It Works

Step-by-step instructions for Claude to follow when this skill is invoked:

1. **Step one.** Describe the first action.
2. **Step two.** Describe the second action.
3. **Step three.** Describe the third action.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name`   | Yes      | Description |
| `--flag` | No       | Description |

## Error Handling

- What to do if X goes wrong
- What to do if Y is missing
```

### Using References

The `references/` subdirectory holds supporting documentation that the skill reads before executing. This is particularly useful for code generation skills:

```
.claude/skills/new-widget/
  SKILL.md
  references/
    widget-examples.md    # Example widget implementations
    widget-patterns.md    # Widget design patterns
```

In the `SKILL.md`, reference these files:

```markdown
## How It Works

1. **Read reference patterns.** Load examples from:
   - `skills/new-widget/references/widget-examples.md`
   - `skills/new-widget/references/widget-patterns.md`

2. **Generate the widget file.** Based on the patterns and the user's
   arguments, create the widget file at the appropriate location.
```

### Tips for Writing Skills

1. **Be explicit.** Tell Claude exactly what files to read, what to generate, and where to put it.
2. **Include examples.** Show what the output should look like for common inputs.
3. **Reference existing patterns.** Point to pattern files and style guides rather than duplicating them.
4. **Handle edge cases.** Describe what to do when arguments are missing, files already exist, or errors occur.
5. **Define output locations.** Specify exactly where generated files should be placed.
6. **Include a completion step.** Tell Claude what to run after generating code (lint, typecheck, tests).

---

## Related Documentation

- [BOOTSTRAP.md](BOOTSTRAP.md) -- How to use bootstrap.sh
- [AGENTS.md](AGENTS.md) -- Agent roles and delegation patterns
- [EVALS.md](EVALS.md) -- How to run quality evaluations
- [ADDING-A-STACK.md](ADDING-A-STACK.md) -- How to add a new stack template
