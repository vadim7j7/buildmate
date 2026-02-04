# Bootstrap Guide

How to use `bootstrap.sh` to generate a `.claude/` agent configuration for your project.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Usage](#detailed-usage)
- [What Gets Installed](#what-gets-installed)
- [Composition Rules](#composition-rules)
- [Post-Install Steps](#post-install-steps)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before running `bootstrap.sh`, ensure the following tools are installed and available on your PATH:

| Tool     | Minimum Version | Purpose                                      |
|----------|-----------------|----------------------------------------------|
| `bash`   | 4.0+            | The bootstrap script uses Bash 4+ features (associative arrays, `set -euo pipefail`) |
| `git`    | 2.x             | Target project must be a git repository (warned if not) |
| `jq`     | 1.6+            | Used for deep-merging `settings.json` files. Without `jq`, stack settings override shared settings instead of merging |

Check your versions:

```bash
bash --version    # Must be 4.0 or higher
git --version     # Any recent version
jq --version      # 1.6 or higher recommended
```

On macOS, the system Bash is version 3.x. Install Bash 4+ via Homebrew:

```bash
brew install bash
```

---

## Quick Start

Clone or download this repository, then run `bootstrap.sh` with a stack name and target project path:

### Rails

```bash
./bootstrap.sh rails /path/to/my-rails-app
```

### React + Next.js

```bash
./bootstrap.sh react-nextjs /path/to/my-react-app
```

### React Native

```bash
./bootstrap.sh react-native /path/to/my-rn-app
```

### Python FastAPI

```bash
./bootstrap.sh python-fastapi /path/to/my-fastapi-app
```

### Multi-Stack Combinations

Combine multiple stacks with commas to create custom configurations:

```bash
./bootstrap.sh rails,react-native /path/to/my-mobile-app           # API + mobile
./bootstrap.sh rails,react-nextjs /path/to/my-fullstack-app        # API + web
./bootstrap.sh rails,react-nextjs,react-native /path/to/my-app     # API + web + mobile
./bootstrap.sh python-fastapi,react-nextjs /path/to/my-python-app  # Python API + web
```

Stacks are layered in order: each stack's agents, skills, hooks, patterns, and styles are merged on top of the previous, with later stacks taking precedence for same-named files.

Each command produces a complete `.claude/` directory and a `CLAUDE.md` file in the target project, ready for use with Claude Code.

---

## Detailed Usage

```
./bootstrap.sh <stacks> <target-path> [--force]
```

### Arguments

| Argument        | Required | Description                                                     |
|-----------------|----------|-----------------------------------------------------------------|
| `<stacks>`      | Yes      | One or more stacks, comma-separated: `rails`, `react-nextjs`, `react-native`, `fullstack`, `python-fastapi` |
| `<target-path>` | Yes      | Absolute or relative path to the target project directory       |
| `--force`       | No       | Overwrite an existing `.claude/` directory in the target        |

### Multi-Stack Examples

```bash
# Single stack
./bootstrap.sh rails /path/to/project

# Two stacks (backend + frontend)
./bootstrap.sh rails,react-nextjs /path/to/project

# Three stacks (backend + web + mobile)
./bootstrap.sh rails,react-nextjs,react-native /path/to/project
```

### Options

| Option              | Description                                                      |
|---------------------|------------------------------------------------------------------|
| `--help`, `-h`      | Show usage information and exit                                  |
| `--force`           | Remove any existing `.claude/` directory before installing        |
| `--preserve-context`| Keep `context/` directory when using `--force` (preserves features, session memory) |

### Examples

```bash
# Basic bootstrap
./bootstrap.sh rails ~/projects/my-api

# Overwrite existing configuration
./bootstrap.sh react-nextjs ~/projects/my-app --force

# Add a new stack while preserving your context/features
./bootstrap.sh rails,react-nextjs,react-native ~/projects/my-app --force --preserve-context

# Inspect output in a temporary directory
./bootstrap.sh rails /tmp/test-output

# Show help
./bootstrap.sh --help
```

---

## What Gets Installed

The bootstrap script runs a four-phase pipeline:

### Phase 1: Validate

- Checks that the stack name is valid (`rails`, `react-nextjs`, `react-native`, `fullstack`, `python-fastapi`)
- Verifies the target path exists and is writable
- Warns if the target is not a git repository
- Fails if `.claude/` already exists (unless `--force` is passed)

### Phase 2: Compose

Builds the final configuration by layering the shared base with the stack-specific overlay in a temporary directory. See [Composition Rules](#composition-rules) below for details.

### Phase 3: Install

- Creates `<target>/.claude/` and copies all composed content into it
- Installs the composed `CLAUDE.md` to the project root:
  - If `CLAUDE.md` already exists and `--force` is not set, the agent instructions are appended
  - If `--force` is set, the existing `CLAUDE.md` is overwritten
  - If no `CLAUDE.md` exists, a new one is created
- Creates `.claude/settings.local.json` with an empty template if it does not already exist

### Phase 4: Post-Install

- Makes all `.sh` files under `.claude/` executable (`chmod +x`)
- Adds `.agent-status/`, `.agent-pipeline/`, and `.agent-eval-results/` to the target's `.gitignore`
- Creates `.gitkeep` files for empty directories (e.g., `context/features/`)
- Prints an installation summary showing counts of agents, skills, hooks, patterns, and styles
- Prints next-steps instructions

### Installed Directory Structure

After bootstrap, your project will contain:

```
<project>/
  .claude/
    agents/              # Agent definition files (.md)
    skills/              # Skill directories (each with SKILL.md and optional references/)
    hooks/               # Hook scripts (.sh)
      session-save.sh    #   Auto-saves context on session end (Stop event)
      session-load.sh    #   Auto-loads context on session start (SessionStart event)
    patterns/            # Code pattern references (stack-specific)
    styles/              # Code style guides (stack-specific)
    context/
      active-work.md     # Auto-saved session context (created on first session end)
      features/          # Feature tracking directory (.gitkeep)
    settings.json        # Merged permissions, hooks configuration
    settings.local.json  # Local overrides template (not committed)
  CLAUDE.md              # Project-level agent instructions
```

### Session Memory

The bootstrap installs two hooks that provide automatic session persistence:

- **`session-save.sh`** (Stop event): After each Claude response, this hook captures the current git state (branch, commits, uncommitted changes), in-progress feature files, and pipeline state. Everything is written to `.claude/context/active-work.md`. Because it runs after every response, the saved context is always up to date even if the session ends unexpectedly.
- **`session-load.sh`** (SessionStart event): When a new session starts, this hook reads `active-work.md` and injects it into the conversation context. If the file is older than 7 days, a staleness warning is shown instead.

Use the `/recap` skill for a more detailed status check at any time. See [SKILLS.md](SKILLS.md) for details.

---

## Composition Rules

The composition layer builds the final configuration by starting with the shared base (`shared/`) and then applying each stack in order. When combining multiple stacks (e.g., `rails,react-native`), each stack is layered on top of the previous. Each type of file has its own merge strategy:

### Agents

**Strategy:** Replace by name, add new.

Stack-specific agent files replace shared agents with the same filename. For example, if both `shared/agents/orchestrator.md` and `stacks/rails/agents/orchestrator.md` exist, the Rails version replaces the shared one entirely. Stack-only agents (e.g., `stacks/rails/agents/backend-developer.md`) are added alongside the remaining shared agents.

### Skills

**Strategy:** Replace by name, add new.

Stack-specific skill directories replace shared skills with the same directory name. For example, if both `shared/skills/test/` and `stacks/rails/skills/test/` exist, the entire Rails `test/` skill directory (including `SKILL.md` and `references/`) replaces the shared one. Stack-only skills (e.g., `stacks/rails/skills/new-service/`) are added alongside the remaining shared skills.

### CLAUDE.md

**Strategy:** Concatenated (shared + all stacks in order).

The shared `CLAUDE.md` is placed first, followed by each stack's `CLAUDE.md` in order, with separators (`---` with a comment) between them. For example, `rails,react-native` would concatenate: shared → rails → react-native.

### settings.json

**Strategy:** Deep-merged with jq (progressive).

All `settings.json` files (shared + each stack in order) are progressively deep-merged:
- **Arrays** (such as `permissions.allow`) are concatenated and deduplicated
- **Objects** are recursively merged, with later stacks winning on conflicts
- **Scalar values** from later stacks override earlier values

For example, `rails,react-native` merges: shared → rails → react-native.

If `jq` is not available, the last stack's `settings.json` is used as-is (no merge) and a warning is printed.

### Hooks

**Strategy:** Replace by name.

Stack-specific hook scripts replace shared hooks with the same filename. For example, if a stack provides `post-edit-format.sh`, it replaces any shared hook with the same name. Stack-only hooks are added.

### Patterns and Styles

**Strategy:** Accumulated from all stacks.

The `patterns/` and `styles/` directories exist only in stack layers -- there is no shared base for them. When combining multiple stacks, files from all stacks are accumulated (not replaced). For example, `rails,react-native` would include both `backend-patterns.md` and `mobile-patterns.md`.

### Summary Table

| File Type      | Merge Strategy                                            |
|----------------|-----------------------------------------------------------|
| Agents         | Later stacks replace earlier by name; new agents added    |
| Skills         | Later stacks replace earlier by name; new skills added    |
| CLAUDE.md      | Concatenated (shared first, then each stack in order)     |
| settings.json  | Deep-merged via jq (arrays concatenated, objects merged)  |
| Hooks          | Later stacks replace earlier by name; new hooks added     |
| Patterns       | Accumulated from all stacks                               |
| Styles         | Accumulated from all stacks                               |

---

## Post-Install Steps

After running `bootstrap.sh`, follow these steps to get started:

### 1. Review the Configuration

```bash
cd /path/to/your-project
cat CLAUDE.md                    # Read agent instructions
ls .claude/                      # See what was installed
ls .claude/agents/               # List available agents
ls .claude/skills/               # List available skills
```

### 2. Customize Settings

Edit `.claude/settings.json` for project-wide settings that apply to all team members. This file should be committed to version control.

Edit `.claude/settings.local.json` for personal overrides (e.g., additional permissions for your workflow). This file should NOT be committed -- add it to `.gitignore` if it is not already there.

### 3. Add Feature Context

Create feature files in `.claude/context/features/` to track ongoing work:

```bash
# Convention: YYYYMMDD-short-slug.md
touch .claude/context/features/20260201-user-auth.md
```

Feature files help the orchestrator agent understand project state and ongoing work. See [AGENTS.md](AGENTS.md) for the feature file format.

### 4. Start Using Agents

Open your project in Claude Code and start working. Use skills by typing `/<skill-name>` in the chat:

```
/test                 # Run the test suite
/review               # Get a code review
/new-service UserSync # Generate a new service (Rails)
```

Use the PM orchestrator for full feature development:

```
Use PM: Build a user authentication system with OAuth support
```

### 5. Commit the Configuration

```bash
git add .claude/ CLAUDE.md .gitignore
git commit -m "Add Claude Code agent configuration (<stack> stack)"
```

---

## Troubleshooting

### "Invalid stack" error

```
[ERROR] Invalid stack: 'my-stack'
[ERROR] Valid stacks are: rails react-nextjs react-native fullstack python-fastapi
```

**Fix:** Use one of the supported stack names. Stack names are case-sensitive and must be lowercase.

### "Target path does not exist" error

```
[ERROR] Target path does not exist: /nonexistent/path
```

**Fix:** Ensure the target directory exists before running bootstrap. The script does not create the target directory.

### "Target already has a .claude/ directory" error

```
[ERROR] Target already has a .claude/ directory
[ERROR] Use --force to overwrite existing configuration.
```

**Fix:** Either remove the existing `.claude/` directory manually, or pass `--force` to overwrite it:

```bash
./bootstrap.sh rails /path/to/project --force
```

### "jq not found" warning

```
[WARN] jq not found. Using stack settings.json as-is (no merge).
```

**Fix:** Install `jq` for proper deep-merging of settings files:

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Fedora
sudo dnf install jq
```

Without `jq`, the stack's `settings.json` replaces the shared one entirely instead of being deep-merged. This means shared permissions may be lost.

### "Target is not a git repository" warning

```
[WARN] Target is not a git repository.
```

**Fix:** Initialize a git repository in the target directory before running bootstrap:

```bash
cd /path/to/project
git init
```

While not strictly required, some agent features (worktrees for parallel execution, diff-based reviews) depend on git.

### Bash version too old (macOS)

If the script fails with syntax errors on macOS, your system Bash is likely version 3.x:

```bash
bash --version
# GNU bash, version 3.2.57(1)-release
```

**Fix:** Install Bash 4+ via Homebrew and run the script with it:

```bash
brew install bash
/opt/homebrew/bin/bash bootstrap.sh rails /path/to/project
```

### Hook scripts not executable

If hook scripts fail to run after bootstrap:

```bash
chmod +x .claude/hooks/*.sh
chmod +x .claude/skills/*/scripts/*.sh
```

The post-install phase should handle this automatically, but if you extract files from an archive, permissions may be lost.

### CLAUDE.md conflicts on re-bootstrap

If you run bootstrap again without `--force`, the agent instructions are appended to the existing `CLAUDE.md`. This can result in duplicate content.

**Fix:** Either use `--force` to overwrite cleanly, or manually edit `CLAUDE.md` to remove duplicates.

---

## Related Documentation

- [AGENTS.md](AGENTS.md) -- Agent roles and delegation patterns
- [SKILLS.md](SKILLS.md) -- Skill descriptions and usage
- [EVALS.md](EVALS.md) -- How to run quality evaluations
- [ADDING-A-STACK.md](ADDING-A-STACK.md) -- How to add a new stack template
