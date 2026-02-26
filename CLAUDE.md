# Buildmate

Bootstrap Claude Code agent configurations for your projects. Composes base agent infrastructure with stack-specific overlays to produce ready-to-use setups.

## Installation

```bash
# Create virtual environment and install
python3 -m venv .venv
.venv/bin/pip install -e .

# Or install with dev dependencies (for testing)
.venv/bin/pip install -e ".[dev]"
```

## Quick Start

```bash
# Bootstrap a project
buildmate rails /path/to/my-rails-app
buildmate nextjs /path/to/my-nextjs-app
buildmate django /path/to/my-django-app

# Use a profile (pre-defined stack combination)
buildmate --profile saas /path/to/my-saas-app
buildmate --profile landing /path/to/my-landing-page

# Customize with options
buildmate nextjs /path/to/app --ui=tailwind --state=zustand
buildmate rails /path/to/app --jobs=good_job --db=postgresql

# Combine stacks manually
buildmate rails+nextjs /path/to/my-fullstack-app
buildmate django+nuxt /path/to/my-fullstack-app
buildmate express+nextjs /path/to/my-fullstack-app
buildmate gin+nextjs /path/to/my-fullstack-app
buildmate phoenix+nuxt /path/to/my-fullstack-app
```

See `README.md` for complete documentation.

## Available Stacks

Stacks are organized into **language parents** and **framework children**. Children inherit agents, quality gates, patterns, styles, and options from their parent via `extends`.

```
ruby (parent)           → rails, sinatra
javascript (parent)     → nextjs, express, nuxt
python (parent)         → flask, fastapi, django
go (parent)             → gin, fiber, chi
elixir (parent)         → phoenix
standalone              → react-native, scraping
```

| Stack | Extends | Description | Agents |
|-------|---------|-------------|--------|
| `ruby` | — | Generic Ruby development | backend-developer, backend-tester, backend-reviewer |
| `rails` | `ruby` | Ruby on Rails API | backend-developer, backend-tester, backend-reviewer |
| `sinatra` | `ruby` | Sinatra Web Application | backend-developer, backend-tester, backend-reviewer |
| `javascript` | — | Generic TypeScript/JS | *(none — children define their own)* |
| `nextjs` | `javascript` | React + Next.js | frontend-developer, frontend-tester, frontend-reviewer |
| `express` | `javascript` | Express.js API | backend-developer, backend-tester, backend-reviewer |
| `nuxt` | `javascript` | Nuxt 3 (Vue) | frontend-developer, frontend-tester, frontend-reviewer |
| `python` | — | Generic Python development | backend-developer, backend-tester, backend-reviewer |
| `flask` | `python` | Flask Web Application | backend-developer, backend-tester, backend-reviewer |
| `fastapi` | `python` | Python FastAPI | backend-developer, backend-tester, backend-reviewer |
| `django` | `python` | Django Web Application | backend-developer, backend-tester, backend-reviewer |
| `go` | — | Generic Go development | backend-developer, backend-tester, backend-reviewer |
| `gin` | `go` | Gin Web Framework | backend-developer, backend-tester, backend-reviewer |
| `fiber` | `go` | Fiber Web Framework | backend-developer, backend-tester, backend-reviewer |
| `chi` | `go` | Chi Router | backend-developer, backend-tester, backend-reviewer |
| `elixir` | — | Generic Elixir development | backend-developer, backend-tester, backend-reviewer |
| `phoenix` | `elixir` | Phoenix Framework | backend-developer, backend-tester, backend-reviewer |
| `react-native` | — | React Native + Expo | mobile-developer, mobile-tester, mobile-code-reviewer |
| `scraping` | — | Web Scraping (Python/Node.js) | scraper-developer, scraper-tester, scraper-reviewer |

## Profiles

Profiles are pre-defined stack combinations with recommended options:

| Profile | Stacks | Use Case |
|---------|--------|----------|
| `landing` | nextjs | Marketing sites, landing pages |
| `saas` | rails + nextjs | SaaS applications |
| `api-only` | rails | API backends |
| `mobile-backend` | rails + react-native | Mobile apps with API |

```bash
buildmate --profiles              # List available profiles
buildmate --profile saas /path/to/app  # Use a profile
```

## Stack Options

Stacks can have configurable options (UI library, state management, etc.):

```bash
buildmate --options nextjs        # Show available options
buildmate nextjs /path/to/app --ui=tailwind --state=zustand
```

## Stack Composition

Combine stacks with `+` for fullstack applications:

```bash
# Rails API + Next.js frontend
buildmate rails+nextjs /path/to/app

# Django + Nuxt frontend
buildmate django+nuxt /path/to/app

# Express API + Next.js frontend
buildmate express+nextjs /path/to/app

# FastAPI + React Native mobile
buildmate fastapi+react-native /path/to/app

# Gin API + Next.js frontend
buildmate gin+nextjs /path/to/app

# Phoenix + Nuxt frontend
buildmate phoenix+nuxt /path/to/app

# Fiber API + Next.js frontend
buildmate fiber+nextjs /path/to/app
```

## Directory Structure

```
buildmate/
├── bootstrap.py              # CLI entry point (also lib/cli.py)
├── README.md                 # Complete documentation
├── schemas/                  # JSON Schema for validation
├── profiles/                 # Pre-defined stack combinations
├── lib/                      # Python library modules
├── base/                     # Base agents, skills, templates
├── stacks/                   # Stack-specific configurations
│   ├── ruby/                # Language parent (extends: none)
│   ├── rails/               # extends: ruby
│   ├── sinatra/             # extends: ruby
│   ├── javascript/          # Language parent (extends: none, no agents)
│   ├── nextjs/              # extends: javascript
│   ├── express/             # extends: javascript
│   ├── nuxt/                # extends: javascript
│   ├── python/              # Language parent (extends: none)
│   ├── flask/               # extends: python
│   ├── fastapi/             # extends: python
│   ├── django/              # extends: python
│   ├── go/                  # Language parent (extends: none)
│   ├── gin/                 # extends: go
│   ├── fiber/               # extends: go
│   ├── chi/                 # extends: go
│   ├── elixir/              # Language parent (extends: none)
│   ├── phoenix/             # extends: elixir
│   ├── react-native/        # Standalone
│   └── scraping/            # Standalone
├── mcp-dashboard/            # Real-time web dashboard
│   ├── server/               # FastAPI backend (REST, WebSocket, process mgmt)
│   └── ui/                   # React + TypeScript + Tailwind frontend
├── tests/                    # Test suite
├── evals/                    # Evaluation configs
└── CLAUDE.md                 # This file
```

## Architecture

### Stack Configuration (stack.yaml)

Each stack is defined by a YAML configuration. Stacks can use `extends` to inherit from a language parent.

**Language parent (standalone):**
```yaml
name: ruby
display_name: Ruby
description: Generic Ruby development with modern tooling
default_model: opus

compatible_with: [nextjs, nuxt, react-native, scraping]

agents:
  - name: backend-developer
    template: agents/backend-developer.md.j2
    model: opus
    tools: [Read, Write, Edit, Bash, Grep, Glob]

skills: [test, review, docs, verify]

quality_gates:
  lint:
    command: bundle exec rubocop
    fix_command: bundle exec rubocop -A
  tests:
    command: bundle exec rspec

patterns:
  - patterns/backend-patterns.md

styles:
  - styles/backend-ruby.md

variables:
  framework: Ruby
  language: Ruby 3.2+
  test_framework: RSpec
```

**Framework child (with inheritance):**
```yaml
name: rails
extends: ruby                    # Inherits agents, gates, patterns, styles, options
display_name: Ruby on Rails API
description: Backend development with Ruby on Rails

compatible_with: [nextjs, nuxt, react-native, scraping]

# Override agents with Rails-specific templates
agents:
  - name: backend-developer
    template: agents/backend-developer.md.j2
    model: opus
    tools: [Read, Write, Edit, Bash, Grep, Glob]

# Rails-specific skills (parent skills inherited automatically)
skills: [new-controller, new-presenter, new-job, db-migrate]

# quality_gates: inherited from ruby
# styles: inherited from ruby

patterns:
  - patterns/auth.md
  - patterns/pagination.md

variables:
  framework: Rails 7+
  orm: ActiveRecord
  # language, test_framework inherited from ruby
```

### Inheritance Rules

| Field | Behavior |
|-------|----------|
| `agents` | Child overrides parent by name; unmatched parent agents inherited |
| `skills` | Union of parent + child (deduplicated) |
| `quality_gates` | Child overrides parent by key; unmatched parent gates inherited |
| `variables` | Child overrides parent by key; unmatched parent values inherited |
| `patterns` | Merged (parent + child) |
| `styles` | Merged (parent + child) |
| `options` | Child overrides parent by key; unmatched parent options inherited |
| `compatible_with` | Union of parent + child |

Only single-level inheritance is supported (no grandparent chains).

### Jinja2 Templates

Agent templates use Jinja2 for dynamic content:

```jinja2
---
name: {{ agent.name }}
tools: {{ agent.tools | join(', ') }}
model: {{ agent.model or default_model }}
---

# {{ agent.name | title }} Agent

You are a {{ variables.framework }} developer.

## Quality Gates

{% for gate_name, gate in stack.quality_gates.items() %}
- **{{ gate_name }}**: `{{ gate.command }}`
{% endfor %}
```

### Adding a New Stack

**Standalone stack:**
1. Create `stacks/my-stack/stack.yaml`
2. Create agent templates in `stacks/my-stack/agents/`
3. Add patterns and styles
4. Copy or create skills
5. Test: `buildmate --validate my-stack`

**Child stack (extending a parent):**
1. Create `stacks/my-framework/stack.yaml` with `extends: parent-name`
2. Only define agents/skills/patterns/variables that differ from parent
3. Create agent templates only for overridden agents
4. Add framework-specific patterns
5. Test: `buildmate --validate my-framework`

See `README.md` for detailed instructions.

## Output Structure

After bootstrapping, the target project will have:

```
my-project/
├── .claude/
│   ├── agents/           # Agent definitions
│   │   ├── orchestrator.md
│   │   ├── grind.md
│   │   ├── eval-agent.md
│   │   ├── security-auditor.md
│   │   └── <stack-specific>.md
│   ├── skills/           # Slash commands
│   ├── patterns/         # Code pattern references
│   ├── styles/           # Style guide references
│   ├── context/
│   │   └── features/     # Feature tracking
│   ├── settings.json
│   └── README.md
└── CLAUDE.md
```

## Key Concepts

### Orchestrator
The orchestrator agent coordinates feature development through a pipeline: Plan → Implement → Test → Review → Eval. It delegates to specialized agents for each stage.

### Quality Gates
Each stack defines quality gates (lint, test, typecheck) that must pass before code review. The grind agent runs fix-verify loops until all gates pass.

### Skills
Skills are slash commands (e.g., `/test`, `/review`, `/new-model`) that invoke specific workflows. Core skills are shared across all stacks; stack-specific skills add domain functionality.

### Feature Tracking
Features are tracked in `.claude/context/features/` as markdown files with status, requirements, and progress.

### Browser Cloning (Frontend Stacks)
Frontend stacks (nextjs, react-native) include browser automation tools for analyzing and cloning website designs into multiple output formats.

**Output Formats:**
- `--format html` - Plain HTML + CSS
- `--format react` - React components + CSS Modules
- `--format nextjs` - Next.js App Router components
- `--format native` - React Native + StyleSheet
- `--format vue` - Vue 3 SFCs
- `--format svelte` - Svelte components

**Skills:**
- `/analyze-site <url>` - Deep analysis of website structure and design tokens
- `/clone-page <url> --format <fmt>` - Clone a webpage in any format

**Agents:**
- `site-analyzer` - Extracts structure, components, design tokens
- `ui-cloner` - Generates production-ready code in any format

**Setup:** Requires MCP browser server configured in `.claude/settings.json`:
```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-puppeteer"]
    }
  }
}
```

### Self-Verification
Agents automatically test their own implementations. After creating an endpoint or component, they verify it works by making real requests or rendering in a browser.

**Verification Flow:**
```
implement → verify → (fail?) → fix → verify again (max 3 retries)
```

**Stack-specific verification:**
- Backend (Rails/FastAPI/Express/Django/Sinatra/Flask/Gin/Fiber/Chi/Phoenix): HTTP requests, validate responses
- Frontend (Next.js/Nuxt): MCP browser, screenshots, DOM checks
- Mobile (React Native): Jest tests, TypeScript checks

**Skill:** `/verify` - manually trigger verification
**Agents:** `backend-verifier`, `frontend-verifier`, `mobile-verifier`

### Web Scraping
The scraping stack provides specialized agents for building robust, ethical web scrapers in Python or Node.js.

**Language Options:**
- Python: Scrapy, BeautifulSoup, Playwright (default)
- Node.js: Puppeteer, Cheerio, Playwright

**Skills:**
- `/new-spider <name>` - Generate Scrapy spider or scraper class
- `/new-scraper <name>` - Generate HTTP or browser-based scraper
- `/analyze-target <url>` - Analyze website structure
- `/test-scraper` - Run comprehensive tests

**Agents:** `scraper-developer`, `scraper-tester`, `scraper-reviewer`

**Patterns:** anti-detection, pagination, authentication, data-validation, error-handling, rate-limiting

**Usage:**
```bash
buildmate scraping /path/to/project --language=python
buildmate scraping /path/to/project --language=nodejs --browser=puppeteer
```

### Git Workflow Automation
Optional automation for branches, commits, and PRs. Configure in `.claude/settings.json`:

```json
{
  "pm": {
    "git_workflow": "full"  // "none" | "branch" | "full"
  }
}
```

**Skills:**
- `/branch <name>` - Create feature branch
- `/ship` - Commit, push, create PR
- `/sync` - Sync branch with main

**PM Integration:** With `git_workflow: "full"`, PM auto-creates branches after plan approval and auto-ships on completion.

**Multi-Repo Support:** For workspaces with multiple git repos:

```json
{
  "pm": {
    "git_workflow": "full",
    "multi_repo": {
      "enabled": true,
      "repositories": {
        "backend": "./backend",
        "web": "./web"
      },
      "stack_repo_map": {
        "rails": "backend",
        "nextjs": "web"
      }
    }
  }
}
```

Creates coordinated branches and linked PRs across repos.

### MCP Dashboard
Real-time web dashboard for monitoring tasks, managing services, and chatting with Claude about your codebase.

**Running:** `cd mcp-dashboard && uv run python -m server.main` → `http://127.0.0.1:8420`

**Server components:**
- `server/main.py` — FastAPI app with REST API, WebSocket, static file serving
- `server/database.py` — SQLite (WAL mode): tasks, activity_log, questions, artifacts, chat_sessions, chat_messages
- `server/queue_manager.py` — Spawns `claude -p` for task orchestration, streams `stream-json` output
- `server/chat_manager.py` — Spawns `claude --print -p` for chat, streams tokens via WebSocket, supports `--resume` for multi-turn
- `server/service_manager.py` — Dev service lifecycle (start/stop/restart)
- `server/mcp_tools.py` — MCP stdio tools for agent integration
- `server/models.py` — Pydantic models (TaskCreate, ChatSendMessage, etc.)

**UI components:**
- `ui/src/context/DashboardContext.tsx` — Tasks, stats, WebSocket state; forwards `chat_*` events to ChatContext
- `ui/src/context/ChatContext.tsx` — Chat sessions, messages, streaming state
- `ui/src/components/ChatPanel.tsx` — Session list + active chat view (right sidebar)
- `ui/src/components/ChatBubble.tsx` — User/assistant message bubbles with markdown rendering

**Chat API routes:** `GET/POST /api/chat/sessions`, `GET/PATCH/DELETE /api/chat/sessions/{id}`, `GET /api/chat/sessions/{id}/messages`, `POST /api/chat/send`, `POST /api/chat/sessions/{id}/cancel`

**Chat WebSocket events:** `chat_delta` (token), `chat_complete` (done), `chat_error` (fail), `chat_cancelled` (stopped)

## CLI Commands

```bash
# List available stacks
buildmate --list

# List available profiles
buildmate --profiles

# Show options for a stack
buildmate --options nextjs

# Validate a stack configuration
buildmate --validate rails

# Bootstrap with options
buildmate rails /path/to/app              # Normal install
buildmate rails /path/to/app --force      # Overwrite existing
buildmate rails /path/to/app --dry-run    # Preview only
buildmate rails /path/to/app --preserve   # Keep existing files

# Use profiles
buildmate --profile saas /path/to/app
buildmate --profile saas /path/to/app --jobs=good_job  # Override profile options

# Multi-stack
buildmate rails+nextjs /path/to/app
buildmate django+nuxt /path/to/app
buildmate express+nextjs /path/to/app
buildmate gin+nextjs /path/to/app
buildmate phoenix+nuxt /path/to/app
```

## Development

```bash
# Run tests
.venv/bin/python -m pytest tests/ -v

# Test all stacks validation
for stack in ruby rails sinatra javascript nextjs express nuxt python flask fastapi django go gin fiber chi elixir phoenix react-native scraping; do
  buildmate --validate $stack
done

# Test bootstrap
mkdir -p /tmp/test-app
buildmate rails /tmp/test-app
ls -la /tmp/test-app/.claude/

# Test multi-stack
buildmate rails+nextjs /tmp/test-fullstack
buildmate django+nuxt /tmp/test-django-nuxt
buildmate express+nextjs /tmp/test-express-nextjs
buildmate gin+nextjs /tmp/test-gin-nextjs
buildmate phoenix+nuxt /tmp/test-phoenix-nuxt
buildmate fiber+nextjs /tmp/test-fiber-nextjs

# Test profiles
buildmate --profile saas /tmp/test-saas
```
