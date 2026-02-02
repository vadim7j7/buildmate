# Agents Template Generator

A template generator that bootstraps `.claude/` agent configurations for projects. It composes a shared (cross-stack) base layer with stack-specific overlays to produce a complete, ready-to-use [Claude Code](https://docs.anthropic.com/en/docs/claude-code) multi-agent setup.

## What It Produces

For any supported stack, the generator installs:

- **Agents** — Named specialists (orchestrator, developer, tester, reviewer, grind) that coordinate through a pipeline
- **Skills** — Slash commands (`/test`, `/review`, `/new-service`, etc.) for common workflows
- **Hooks** — Shell scripts that run automatically on events (format on save, lint on edit, session persistence)
- **Patterns** — Code pattern references that agents read before generating code
- **Styles** — Style guides enforced by linters and followed by agents
- **Context** — Feature tracking files for pipeline state
- **Settings** — Permissions, hook configuration, and tool access

## Supported Stacks

| Stack | Command | Description |
|-------|---------|-------------|
| `rails` | `./bootstrap.sh rails /path/to/project` | Ruby on Rails (RSpec, Rubocop, Sidekiq) |
| `react-nextjs` | `./bootstrap.sh react-nextjs /path/to/project` | React + Next.js (Playwright, ESLint, TypeScript) |
| `react-native` | `./bootstrap.sh react-native /path/to/project` | React Native (Jest, ESLint, Zustand) |
| `fullstack` | `./bootstrap.sh fullstack /path/to/project` | Rails API + React frontend combined |
| `python-fastapi` | `./bootstrap.sh python-fastapi /path/to/project` | Python FastAPI (pytest, Ruff, mypy, SQLAlchemy, Celery) |

## Quick Start

```bash
# 1. Clone this repo
git clone <repo-url> agents
cd agents

# 2. Bootstrap a stack into your project
./bootstrap.sh python-fastapi ~/Projects/my-api

# 3. Open in Claude Code and start working
cd ~/Projects/my-api
# Type "Use PM: <task>" or use slash commands like /test, /new-router, etc.
```

To overwrite an existing `.claude/` directory:

```bash
./bootstrap.sh python-fastapi ~/Projects/my-api --force
```

## How It Works

The generator runs a four-phase pipeline:

```
Validate --> Compose --> Install --> Post-Install
```

1. **Validate** — Checks the stack name, target path, git repo, and existing `.claude/`
2. **Compose** — Copies `shared/` as the base, overlays `stacks/<stack>/` on top using merge rules (agents/skills/hooks replace by name, `CLAUDE.md` is concatenated, `settings.json` is deep-merged)
3. **Install** — Copies the composed output to `<target>/.claude/` and `<target>/CLAUDE.md`
4. **Post-Install** — Makes hooks executable, updates `.gitignore`, prints summary

## Repository Structure

```
agents/
├── bootstrap.sh                # Main entry point
├── bootstrap-lib/              # Pipeline scripts
│   ├── validate.sh             #   Input validation
│   ├── compose.sh              #   Shared + stack composition
│   ├── install.sh              #   Copy to target project
│   └── post-install.sh         #   Permissions, gitignore, summary
├── shared/                     # Cross-stack base layer
│   ├── agents/                 #   eval-agent, security-auditor, etc.
│   ├── skills/                 #   delegate, parallel, sequential, docs, eval, etc.
│   ├── hooks/                  #   session-save, session-load, pre-bash-safety
│   └── context/                #   Feature tracking template
├── stacks/                     # Stack-specific overlays
│   ├── rails/                  #   Rails agents, skills, hooks, patterns, styles
│   ├── react-nextjs/           #   React/Next.js agents, skills, hooks, patterns
│   ├── react-native/           #   React Native agents, skills, hooks
│   ├── fullstack/              #   Fullstack (Rails + React) agents
│   └── python-fastapi/         #   FastAPI agents, skills, hooks, patterns, styles
├── docs/                       # Documentation
│   ├── BOOTSTRAP.md            #   Detailed bootstrap usage and troubleshooting
│   ├── ADDING-A-STACK.md       #   How to create a new stack template
│   ├── AGENTS.md               #   Agent roles and delegation patterns
│   ├── SKILLS.md               #   Skill descriptions and usage
│   └── EVALS.md                #   Quality evaluation system
├── CLAUDE.md                   #   Project instructions for Claude Code
└── README.md                   #   This file
```

## Agent Pipeline

After bootstrapping, every non-trivial task flows through:

```
Plan --> Implement --> Test --> Review --> Eval --> Security
```

The **orchestrator** (PM) coordinates this by delegating to specialist agents. The pipeline operates in two modes:

**Phase 1 — Interactive Planning:** The orchestrator asks clarifying questions, explores the codebase, creates a feature file, and presents the plan for user approval.

**Phases 2+ — Autonomous Execution:** After the user approves the plan, the orchestrator chains Task calls without stopping. The **grind agent** handles fix-verify loops — running quality gates, reading errors, fixing code, and re-running until everything passes. The pipeline only stops if grind can't converge, the reviewer flags a blocker, or infrastructure fails.

You trigger the full pipeline with:

```
Use PM: Build a user authentication system with OAuth
```

Or use individual skills directly:

```
/test                          # Run the test suite
/review                        # Code review changed files
/new-router projects           # Generate a CRUD router (FastAPI)
/new-service UserSync          # Generate a service (Rails)
/new-component Button          # Generate a component (React)
```

### Agents Summary

| Agent | Scope | Role |
|-------|-------|------|
| **PM (Orchestrator)** | All stacks | Workflow guide — plans features, delegates to specialists, tracks progress |
| **Developer** | Per stack | Writes production code (services, models, components, routers) |
| **Tester** | Per stack | Writes and runs tests (RSpec, Jest, pytest) |
| **Reviewer** | Per stack | Code review against conventions and best practices |
| **Grind** | All stacks | Fix-verify loops — runs commands, reads errors, fixes code, repeats until pass |
| **Eval Agent** | All stacks | Scores code quality across 5 dimensions with weighted formula |
| **Security Auditor** | All stacks | OWASP Top 10 vulnerability scanning |
| **Regression Monitor** | All stacks | Pre-merge regression checking |
| **Documentation Specialist** | All stacks | Generates inline docs, API docs, and architecture overviews |

## Prerequisites

| Tool | Version | Required |
|------|---------|----------|
| `bash` | 4.0+ | Yes |
| `git` | 2.x | Recommended |
| `jq` | 1.6+ | Recommended (for settings.json deep-merge) |

On macOS, the system bash is 3.x. Install bash 4+ via `brew install bash`.

## Adding a New Stack

See [docs/ADDING-A-STACK.md](docs/ADDING-A-STACK.md) for the full guide. In short:

```bash
mkdir -p stacks/my-stack/{agents,skills,hooks,patterns,styles}
# Add agents, skills, hooks, patterns, styles, CLAUDE.md, settings.json
# Add "my-stack" to VALID_STACKS_STR in bootstrap-lib/validate.sh
./bootstrap.sh my-stack /tmp/test-output  # verify
```

## Documentation

| Doc | Description |
|-----|-------------|
| [BOOTSTRAP.md](docs/BOOTSTRAP.md) | Detailed usage, composition rules, troubleshooting |
| [ADDING-A-STACK.md](docs/ADDING-A-STACK.md) | Step-by-step guide for creating new stack templates |
| [AGENTS.md](docs/AGENTS.md) | Agent roles, delegation patterns, pipeline details |
| [SKILLS.md](docs/SKILLS.md) | All available slash commands and their usage |
| [EVALS.md](docs/EVALS.md) | Quality evaluation rubrics and scoring |
