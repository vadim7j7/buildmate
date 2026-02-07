# Buildmate

Bootstrap Claude Code agent configurations for your projects. Composes base agent infrastructure with stack-specific overlays to produce ready-to-use setups.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow?style=flat&logo=buy-me-a-coffee)](https://buymeacoffee.com/vadim7j7)
[![CI](https://github.com/vadim7j7/buildmate/actions/workflows/ci.yml/badge.svg)](https://github.com/vadim7j7/buildmate/actions/workflows/ci.yml)

## Features

- **YAML-driven configuration** - Each stack is defined by a `stack.yaml` file
- **Jinja2 templating** - Dynamic agent generation with variables and conditions
- **Stack composition** - Combine multiple stacks (e.g., `rails+nextjs` for fullstack)
- **Stack options** - Configurable choices per stack (UI library, state management, etc.)
- **Profiles** - Pre-defined stack combinations for common project types (SaaS, landing, API)
- **JSON Schema validation** - Validates stack configurations before rendering
- **Compatibility checking** - Warns about incompatible stack combinations
- **Dry-run mode** - Preview what will be installed without making changes
- **Quality gates** - Stack-specific linting, testing, and type checking commands

## Installation

```bash
# Clone the repository
git clone <repo-url> agents
cd agents

# Create virtual environment and install
python3 -m venv .venv
.venv/bin/pip install -e .

# Or install with dev dependencies (for testing)
.venv/bin/pip install -e ".[dev]"
```

## Quick Start

```bash
# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Bootstrap a project
python bootstrap.py rails /path/to/my-rails-app
python bootstrap.py nextjs /path/to/my-nextjs-app

# Use a profile (pre-defined stack combination)
python bootstrap.py --profile saas /path/to/my-saas-app
python bootstrap.py --profile landing /path/to/my-landing-page

# Customize with options
python bootstrap.py nextjs /path/to/app --ui=tailwind --state=zustand
python bootstrap.py rails /path/to/app --jobs=good_job --db=postgresql

# Combine stacks manually
python bootstrap.py rails+nextjs /path/to/my-fullstack-app
```

## Available Stacks

| Stack | Description | Agents | Key Skills |
|-------|-------------|--------|------------|
| `rails` | Ruby on Rails API | backend-developer, backend-tester, backend-reviewer | new-model, new-controller, new-service, db-migrate |
| `nextjs` | React + Next.js | frontend-developer, frontend-tester, frontend-reviewer | new-component, new-page, new-container, new-form |
| `react-native` | React Native + Expo | mobile-developer, mobile-tester, mobile-code-reviewer | new-screen, new-store, new-query, platform-check |
| `fastapi` | Python FastAPI | backend-developer, backend-tester, backend-reviewer | new-router, new-schema, new-model, new-service |

## Profiles

Profiles are pre-defined stack combinations with recommended options:

| Profile | Stacks | Options | Use Case |
|---------|--------|---------|----------|
| `landing` | nextjs | ui=tailwind, state=none | Marketing sites, landing pages |
| `saas` | rails + nextjs | Full configuration | SaaS applications |
| `api-only` | rails | jobs=sidekiq, db=postgresql | API backends |
| `mobile-backend` | rails + react-native | jobs=sidekiq, db=postgresql | Mobile apps with API |

```bash
# List available profiles
python bootstrap.py --profiles

# Use a profile
python bootstrap.py --profile saas /path/to/app

# Override profile options
python bootstrap.py --profile saas /path/to/app --jobs=good_job
```

## Stack Options

Stacks can have configurable options. View available options with `--options`:

```bash
python bootstrap.py --options nextjs
```

### Next.js Options

| Option | Choices | Default |
|--------|---------|---------|
| `--ui` | mantine, tailwind, shadcn | mantine |
| `--state` | zustand, context, none | zustand |

### Rails Options

| Option | Choices | Default |
|--------|---------|---------|
| `--jobs` | sidekiq, good_job, solid_queue, active_job | sidekiq |
| `--db` | postgresql, mysql, sqlite | postgresql |

## CLI Usage

```bash
# List available stacks
python bootstrap.py --list

# List available profiles
python bootstrap.py --profiles

# Show options for a stack
python bootstrap.py --options nextjs

# Validate a stack configuration
python bootstrap.py --validate rails

# Bootstrap with options
python bootstrap.py rails /path/to/app              # Normal install
python bootstrap.py rails /path/to/app --force      # Overwrite existing .claude/
python bootstrap.py rails /path/to/app --dry-run    # Preview without installing
python bootstrap.py rails /path/to/app --preserve   # Keep existing files, add new ones

# Multi-stack composition
python bootstrap.py rails+nextjs /path/to/app       # Fullstack Rails + Next.js
python bootstrap.py fastapi+react-native /path/to/app  # API + Mobile
```

## Directory Structure

```
agents/
├── bootstrap.py              # Main CLI entry point
├── pyproject.toml            # Package configuration
├── README.md                 # This file
├── CLAUDE.md                 # Project instructions for Claude
├── schemas/
│   ├── stack.schema.json     # JSON Schema for stack.yaml validation
│   └── profile.schema.json   # JSON Schema for profile.yaml validation
├── profiles/                 # Pre-defined stack combinations
│   ├── landing.yaml          # Next.js + Tailwind for landing pages
│   ├── saas.yaml             # Rails + Next.js full SaaS setup
│   ├── api-only.yaml         # Rails API backend
│   └── mobile-backend.yaml   # Rails + React Native
├── lib/
│   ├── __init__.py           # Package version
│   ├── schema.py             # Schema validation utilities
│   ├── config.py             # Configuration loading and composition
│   ├── renderer.py           # Jinja2 template rendering
│   └── installer.py          # Install rendered output to target
├── base/
│   ├── agents/               # Base agent templates (shared across all stacks)
│   │   ├── orchestrator.md.j2    # PM/workflow coordinator
│   │   ├── grind.md.j2           # Fix-verify loop agent
│   │   ├── eval-agent.md.j2      # Quality evaluation agent
│   │   └── security-auditor.md.j2 # Security audit agent
│   ├── skills/               # Core skills (always included)
│   │   ├── delegate/         # Smart task delegation
│   │   ├── docs/             # Documentation generation
│   │   ├── eval/             # Quality evaluation
│   │   ├── parallel/         # Parallel worktree execution
│   │   ├── recap/            # Session context loading
│   │   ├── review/           # Code review
│   │   ├── security/         # Security audit
│   │   ├── sequential/       # Pipeline stages
│   │   └── test/             # Test running
│   ├── CLAUDE.md.j2          # Project CLAUDE.md template
│   ├── README.md.j2          # .claude/README.md template
│   └── settings.json         # Base settings
├── stacks/
│   ├── rails/
│   │   ├── stack.yaml        # Stack configuration
│   │   ├── agents/           # Rails-specific agent templates
│   │   ├── skills/           # Rails-specific skills
│   │   ├── patterns/         # Code pattern references
│   │   └── styles/           # Style guide references
│   ├── nextjs/
│   │   └── ...
│   ├── react-native/
│   │   └── ...
│   └── fastapi/
│       └── ...
├── tests/                    # Test suite
└── evals/                    # Evaluation configs
```

## Stack Configuration (stack.yaml)

Each stack is defined by a `stack.yaml` file:

```yaml
name: rails
display_name: Ruby on Rails API
description: Backend development with Ruby on Rails

default_model: opus

# Which stacks can be combined with this one
compatible_with:
  - nextjs
  - react-native

# Agent definitions
agents:
  - name: backend-developer
    template: agents/backend-developer.md.j2
    description: Senior Rails developer for production code
    model: opus
    tools:
      - Read
      - Write
      - Edit
      - Bash
      - Grep
      - Glob

  - name: backend-tester
    template: agents/backend-tester.md.j2
    description: RSpec testing specialist
    model: sonnet
    tools:
      - Read
      - Write
      - Edit
      - Bash
      - Grep
      - Glob

# Skills to include (from this stack's skills/ directory)
skills:
  - test
  - review
  - docs
  - new-model
  - new-controller

# Quality gates (commands that must pass)
quality_gates:
  lint:
    command: bundle exec rubocop
    fix_command: bundle exec rubocop -A
    description: Ruby linting
  tests:
    command: bundle exec rspec
    description: RSpec test suite

# Working directory relative to project root
working_dir: "."

# Pattern and style references
patterns:
  - patterns/backend-patterns.md

styles:
  - styles/backend-ruby.md

# Variables available in templates
variables:
  framework: Ruby on Rails 7+
  language: Ruby
  test_framework: RSpec
  orm: ActiveRecord
```

## Writing Agent Templates

Agent templates use Jinja2 syntax. Available variables:

```jinja2
{{ agent.name }}           # Agent name from stack.yaml
{{ agent.description }}    # Agent description
{{ agent.tools | join(', ') }}  # Comma-separated tools list
{{ agent.model }}          # Model (opus, sonnet, haiku)
{{ default_model }}        # Stack's default model

{{ stack.name }}           # Stack name
{{ stack.display_name }}   # Human-readable stack name
{{ stack.quality_gates }}  # Dict of quality gates
{{ stack.patterns }}       # List of pattern files
{{ stack.styles }}         # List of style files

{{ variables.framework }}  # Custom variables from stack.yaml
{{ variables.language }}
{{ variables.test_framework }}

{% for gate_name, gate in stack.quality_gates.items() %}
- {{ gate_name }}: {{ gate.command }}
{% endfor %}

{% for pattern in stack.patterns %}
- patterns/{{ pattern | basename }}
{% endfor %}
```

### Escaping Code Examples

When including code examples with curly braces (TypeScript, JavaScript, etc.), wrap them in `{% raw %}...{% endraw %}`:

```jinja2
{% raw %}
```typescript
const store = create<State>()((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
}));
```
{% endraw %}
```

## Adding a New Stack

### Option 1: Use /new-stack Skill (Recommended)

When working in this repo, use the `/new-stack` skill to generate a complete stack:

```
/new-stack django
/new-stack laravel
/new-stack flutter
```

This will:
- Prompt for stack details (framework, language, quality gates, etc.)
- Generate all required files following existing patterns
- Update README.md with the new stack
- Validate the stack configuration

See `.claude/skills/new-stack/SKILL.md` for the complete workflow.

### Option 2: Manual Creation

1. **Create the stack directory:**
   ```bash
   mkdir -p stacks/my-stack/{agents,skills,patterns,styles}
   ```

2. **Create `stack.yaml`:**
   ```yaml
   name: my-stack
   display_name: My Stack
   description: Description of my stack

   default_model: opus

   compatible_with:
     - rails  # List compatible stacks

   agents:
     - name: my-developer
       template: agents/my-developer.md.j2
       description: Developer agent
       model: opus
       tools: [Read, Write, Edit, Bash, Grep, Glob]

   skills:
     - test
     - review

   quality_gates:
     lint:
       command: npm run lint
       description: Linting

   patterns:
     - patterns/my-patterns.md

   styles:
     - styles/my-style.md

   variables:
     framework: My Framework
     language: My Language
   ```

3. **Create agent templates in `agents/`:**
   ```jinja2
   ---
   name: my-developer
   description: Developer for My Stack
   tools: {{ agent.tools | join(', ') }}
   model: {{ agent.model or default_model }}
   ---

   # My Developer Agent

   You are a developer specializing in {{ variables.framework }}.

   ## Before Writing Code

   Read these files first:
   {% for pattern in stack.patterns %}
   - `patterns/{{ pattern | basename }}`
   {% endfor %}

   ## Quality Gates

   {% for gate_name, gate in stack.quality_gates.items() %}
   - **{{ gate_name }}**: `{{ gate.command }}`
   {% endfor %}
   ```

4. **Add patterns and styles:**
   - Create `patterns/my-patterns.md` with code examples
   - Create `styles/my-style.md` with style conventions

5. **Add skills (optional):**
   - Copy skills from another stack or create new ones
   - Each skill is a directory with `SKILL.md` and optional `references/`

6. **Test:**
   ```bash
   python bootstrap.py --validate my-stack
   python bootstrap.py my-stack /tmp/test-my-stack
   ```

## Stack Composition

When composing multiple stacks (e.g., `rails,nextjs`):

1. **Agents are merged** - All agents from all stacks are included
2. **Skills are merged** - All skills from all stacks are included
3. **Quality gates are merged** - All gates from all stacks
4. **Patterns/styles are merged** - All pattern and style files
5. **Compatibility is checked** - Warning if stacks aren't in each other's `compatible_with`

The orchestrator template automatically detects multiple stacks and generates appropriate delegation logic for each.

## Output Structure

After bootstrapping, the target project will have:

```
my-project/
├── .claude/
│   ├── agents/           # Rendered agent definitions
│   │   ├── orchestrator.md
│   │   ├── grind.md
│   │   ├── eval-agent.md
│   │   ├── security-auditor.md
│   │   └── <stack-specific-agents>.md
│   ├── skills/           # Core + stack-specific skills
│   │   ├── delegate/
│   │   ├── test/
│   │   ├── review/
│   │   ├── recap/        # Session context loading
│   │   └── ...
│   ├── hooks/            # Lifecycle hooks
│   │   ├── track-changes.sh
│   │   ├── task-complete.sh
│   │   ├── session-end.sh
│   │   └── session-save.sh
│   ├── patterns/         # Code pattern references
│   ├── styles/           # Style guide references
│   ├── context/
│   │   ├── features/     # Feature tracking directory
│   │   ├── active-work.md      # Previous session state (auto-generated)
│   │   ├── session-summary.md  # Last session summary (auto-generated)
│   │   └── agent-activity.log  # Activity log (auto-generated)
│   ├── settings.json     # Shared settings
│   ├── settings.local.json  # Local settings (gitignored)
│   └── README.md         # Usage instructions
└── CLAUDE.md             # Project-level instructions
```

## Session Continuity

The bootstrap includes hooks that track agent activity and enable session continuity.

### How It Works

```
Session 1                              Session 2
─────────                              ─────────
Work on feature                        Run /recap or start PM workflow
    ↓                                      ↓
Hooks track activity:                  Load saved context:
  • track-changes.sh (file edits)        • active-work.md
  • task-complete.sh (tasks)             • session-summary.md
    ↓                                      • agent-activity.log
Session ends                               ↓
    ↓                                  Continue where you left off
session-end.sh saves summary
```

### Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `track-changes.sh` | PostToolUse: Edit\|Write | Logs file modifications |
| `task-complete.sh` | PostToolUse: Task | Logs subagent task completions |
| `session-end.sh` | Stop | Generates session summary |
| `session-save.sh` | Manual | Saves active work context |

### Loading Previous Context

**Option 1: Run `/recap`**

```
/recap
```

Returns a formatted summary of previous session state, in-progress features, and suggested next steps.

**Option 2: Use PM workflow**

The orchestrator's Phase 1.0 automatically checks for previous session context before planning.

### Generated Files

| File | Content | Gitignored |
|------|---------|------------|
| `context/active-work.md` | Branch, uncommitted changes, in-progress features | No |
| `context/session-summary.md` | Session stats, recent activity | Yes |
| `context/agent-activity.log` | Timestamped file edits and task completions | Yes |

## Development

```bash
# Create/activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Validate all stacks
python bootstrap.py --validate rails
python bootstrap.py --validate nextjs
python bootstrap.py --validate react-native
python bootstrap.py --validate fastapi

# Test bootstrap
mkdir -p /tmp/test-app
python bootstrap.py rails /tmp/test-app
ls -la /tmp/test-app/.claude/
```

## License

[Polyform Noncommercial 1.0.0](LICENSE) - Free for personal and non-commercial use.

## Support

If you find this project useful, consider supporting its development:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow?style=for-the-badge&logo=buy-me-a-coffee)](https://buymeacoffee.com/vadim7j7)
