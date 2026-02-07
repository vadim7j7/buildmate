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
# Activate virtual environment
source .venv/bin/activate

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

See `README.md` for complete documentation.

## Available Stacks

| Stack | Description | Agents |
|-------|-------------|--------|
| `rails` | Ruby on Rails API | backend-developer, backend-tester, backend-reviewer |
| `nextjs` | React + Next.js | frontend-developer, frontend-tester, frontend-reviewer |
| `react-native` | React Native + Expo | mobile-developer, mobile-tester, mobile-code-reviewer |
| `fastapi` | Python FastAPI | backend-developer, backend-tester, backend-reviewer |

## Profiles

Profiles are pre-defined stack combinations with recommended options:

| Profile | Stacks | Use Case |
|---------|--------|----------|
| `landing` | nextjs | Marketing sites, landing pages |
| `saas` | rails + nextjs | SaaS applications |
| `api-only` | rails | API backends |
| `mobile-backend` | rails + react-native | Mobile apps with API |

```bash
python bootstrap.py --profiles              # List available profiles
python bootstrap.py --profile saas /path/to/app  # Use a profile
```

## Stack Options

Stacks can have configurable options (UI library, state management, etc.):

```bash
python bootstrap.py --options nextjs        # Show available options
python bootstrap.py nextjs /path/to/app --ui=tailwind --state=zustand
```

## Stack Composition

Combine stacks with `+` for fullstack applications:

```bash
# Rails API + Next.js frontend
.venv/bin/python bootstrap.py rails+nextjs /path/to/app

# FastAPI + React Native mobile
.venv/bin/python bootstrap.py fastapi+react-native /path/to/app
```

## Directory Structure

```
agents/
├── bootstrap.py              # Main CLI entry point
├── README.md                 # Complete documentation
├── schemas/                  # JSON Schema for validation
├── profiles/                 # Pre-defined stack combinations
├── lib/                      # Python library modules
├── base/                     # Base agents, skills, templates
├── stacks/                   # Stack-specific configurations
│   ├── rails/
│   ├── nextjs/
│   ├── react-native/
│   └── fastapi/
├── tests/                    # Test suite
├── evals/                    # Evaluation configs
└── CLAUDE.md                 # This file
```

## Architecture

### Stack Configuration (stack.yaml)

Each stack is defined by a YAML configuration:

```yaml
name: rails
display_name: Ruby on Rails API
description: Backend development with Ruby on Rails

default_model: opus

compatible_with:
  - nextjs
  - react-native

agents:
  - name: backend-developer
    template: agents/backend-developer.md.j2
    model: opus
    tools: [Read, Write, Edit, Bash, Grep, Glob]

skills:
  - test
  - review
  - new-model
  - new-controller

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
  framework: Ruby on Rails 7+
  language: Ruby
  test_framework: RSpec
```

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

1. Create `stacks/my-stack/stack.yaml`
2. Create agent templates in `stacks/my-stack/agents/`
3. Add patterns and styles
4. Copy or create skills
5. Test: `python bootstrap.py --validate my-stack`

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

## CLI Commands

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
python bootstrap.py rails /path/to/app --force      # Overwrite existing
python bootstrap.py rails /path/to/app --dry-run    # Preview only
python bootstrap.py rails /path/to/app --preserve   # Keep existing files

# Use profiles
python bootstrap.py --profile saas /path/to/app
python bootstrap.py --profile saas /path/to/app --jobs=good_job  # Override profile options

# Multi-stack
python bootstrap.py rails+nextjs /path/to/app
```

## Development

```bash
# Run tests
.venv/bin/python -m pytest tests/ -v

# Test all stacks validation
for stack in rails nextjs react-native fastapi; do
  python bootstrap.py --validate $stack
done

# Test bootstrap
mkdir -p /tmp/test-app
python bootstrap.py rails /tmp/test-app
ls -la /tmp/test-app/.claude/

# Test multi-stack
mkdir -p /tmp/test-fullstack
python bootstrap.py rails+nextjs /tmp/test-fullstack

# Test profiles
python bootstrap.py --profile saas /tmp/test-saas
```
