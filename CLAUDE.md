# Agents Template Generator

## Project Overview

This is a template generator that bootstraps `.claude/` agent configurations for projects. It composes shared (cross-stack) agent infrastructure with stack-specific overlays to produce a complete, ready-to-use Claude Code agent setup.

The generator produces:
- **Named agents** with specific responsibilities (orchestrator, implementer, reviewer, etc.)
- **Skills** (slash commands) for common development workflows
- **Hooks** for pre/post-command automation
- **Context files** for feature tracking and project state
- **Settings** for permissions, allowed tools, and MCP configuration
- **Patterns and styles** for code generation consistency

## Directory Structure

```
agents/
  bootstrap.sh              # Main entry point - run this to generate configs
  bootstrap-lib/            # Library scripts used by bootstrap.sh
    validate.sh             #   Input validation (stack, path, git, conflicts)
    compose.sh              #   Composition logic (shared + stack overlay)
    install.sh              #   Copy composed output to target project
    post-install.sh         #   Post-install tasks (permissions, gitignore, summary)
  shared/                   # Cross-stack base layer (copied first)
    agents/                 #   Agent definitions shared across all stacks
    skills/                 #   Shared skills (delegate, docs, eval, parallel, etc.)
    context/                #   Context directory template
      features/             #   Feature tracking directory
    hooks/                  #   Shared hook scripts
  stacks/                   # Stack-specific overlays (applied on top of shared)
    rails/                  #   Ruby on Rails stack
      agents/               #     Rails-specific agent overrides
      skills/               #     Rails skills (new-model, new-controller, etc.)
      hooks/                #     Rails-specific hooks
      patterns/             #     Rails code patterns
      styles/               #     Rails code style guides
    react-nextjs/           #   React + Next.js stack
      agents/               #     React/Next-specific agent overrides
      skills/               #     React skills (new-component, new-page, etc.)
      hooks/                #     React-specific hooks
      patterns/             #     React code patterns
      styles/               #     TypeScript + React style guides
    react-native/           #   React Native stack
      agents/               #     RN-specific agent overrides
      skills/               #     RN skills (new-screen, new-store, etc.)
      hooks/                #     RN-specific hooks
      patterns/             #     React Native code patterns
      styles/               #     React Native style guides
    fullstack/              #   Fullstack (Rails + React) stack
      agents/               #     Fullstack-specific agent overrides
    python-fastapi/         #   Python FastAPI stack
      agents/               #     FastAPI-specific agent overrides
      skills/               #     FastAPI skills (new-router, new-schema, etc.)
      hooks/                #     FastAPI-specific hooks
      patterns/             #     FastAPI code patterns
      styles/               #     Python style guides
  docs/                     # Documentation for the generator itself
  evals/                    # Evaluation configs and test cases
  CLAUDE.md                 # This file - project-level instructions
  .gitignore                # Git ignore rules for the generator
```

## How bootstrap.sh Works

The bootstrap script follows a four-phase pipeline:

### Phase 1: Validate
- Checks that the requested stack name is one of: `rails`, `react-nextjs`, `react-native`, `fullstack`, `python-fastapi`
- Verifies the target path exists and is a directory
- Warns if the target is not a git repository
- Checks for existing `.claude/` directory (fails unless `--force` is passed)

### Phase 2: Compose
This is the core logic. It builds the final configuration by layering:

1. **Copy shared/ as the base layer** into a temporary directory
2. **Apply each stack in order** (for multi-stack, e.g., `rails,react-native`):
   - **Agents**: Stack-specific agents replace shared/previous ones with the same name; new agents are added
   - **Skills**: Stack-specific skills replace shared/previous ones with the same name; new skills are added
   - **Hooks**: Stack-specific hooks replace shared/previous ones with the same name
   - **Patterns/Styles**: Accumulated from all stacks (no replacement)
3. **Merge CLAUDE.md** from shared + all stacks (concatenated with separators)
4. **Deep-merge settings.json** from shared + all stacks (arrays concatenated, objects recursively merged)
5. **Create context/ and context/features/** directories for feature tracking

When combining multiple stacks, later stacks take precedence for same-named agents/skills/hooks.

### Phase 3: Install
- Copies the composed temp directory to `<target>/.claude/`
- Copies or appends the composed CLAUDE.md to `<target>/CLAUDE.md`
- Creates `.claude/settings.local.json` from template if it does not exist

### Phase 4: Post-Install
- Makes all `.sh` files in `.claude/` executable
- Adds `.agent-status/`, `.agent-pipeline/`, `.agent-eval-results/` to the target's `.gitignore`
- Creates `context/features/.gitkeep` for empty directory tracking
- Prints a summary of what was installed and next steps

## Available Stacks

| Stack | Description | Key Skills |
|-------|-------------|------------|
| `rails` | Ruby on Rails applications | new-model, new-controller, new-service, new-migration, db-migrate, new-job, new-presenter, new-spec |
| `react-nextjs` | React + Next.js applications | new-component, new-page, new-container, new-context, new-form, new-api-service, component-gen |
| `react-native` | React Native mobile apps | new-screen, new-rn-component, new-store, new-query, new-db-query, platform-check |
| `fullstack` | Combined Rails API + React frontend | Combines rails + react-nextjs skills (legacy, use `rails,react-nextjs`) |
| `python-fastapi` | Python FastAPI applications | new-router, new-schema, new-model, new-service, new-migration, db-migrate, new-test, new-task |

**Multi-stack combinations:** Use commas to combine stacks (e.g., `rails,react-native` for API + mobile).

## How to Add a New Stack Template

1. Create a new directory under `stacks/`:
   ```
   mkdir -p stacks/my-stack/{agents,skills,hooks,patterns,styles}
   ```

2. Add stack-specific agents in `stacks/my-stack/agents/`. Use the same filenames as shared agents to override them, or new filenames to add stack-only agents.

3. Add stack-specific skills in `stacks/my-stack/skills/`. Each skill is a directory containing its markdown instructions and optional `references/` subdirectory.

4. Optionally add:
   - `stacks/my-stack/CLAUDE.md` -- stack-specific instructions (appended to shared CLAUDE.md)
   - `stacks/my-stack/settings.json` -- stack-specific settings (deep-merged with shared)
   - `stacks/my-stack/hooks/` -- stack-specific hook scripts
   - `stacks/my-stack/patterns/` -- code pattern references
   - `stacks/my-stack/styles/` -- code style guides

5. Add the stack name to the `VALID_STACKS` array in `bootstrap-lib/validate.sh` and `bootstrap.sh`.

6. Test by running:
   ```bash
   ./bootstrap.sh my-stack /path/to/test-project
   ```

## Key Patterns

### Orchestrator is a Workflow Guide, Not Spawnable
The orchestrator agent is a workflow guide that coordinates feature development. It is read by the human or by Claude as context -- it does not spawn sub-agents. It defines the sequence of steps, quality gates, and handoff points.

### Named Agents
Each agent has a specific name and responsibility. Agent files are markdown documents that define the agent's role, capabilities, constraints, and workflows. Examples: orchestrator, implementer, reviewer, tester.

### Feature Tracking
The `context/features/` directory holds per-feature state files that track progress through the development pipeline. Features move through stages: planned, in-progress, review, complete.

### Quality Gates
Agents enforce quality gates at stage transitions. Code must pass linting, type checking, and tests before moving from implementation to review. Reviews must be approved before marking complete.

### Agent Pipeline
The `.agent-pipeline/` directory (gitignored) holds transient pipeline state for multi-agent workflows. This includes handoff files, intermediate results, and coordination state.

## Development Commands

```bash
# Bootstrap a single stack to a target project
./bootstrap.sh rails /path/to/my-rails-app
./bootstrap.sh react-nextjs /path/to/my-react-app
./bootstrap.sh react-native /path/to/my-rn-app
./bootstrap.sh python-fastapi /path/to/my-fastapi-app

# Combine multiple stacks (comma-separated, layered in order)
./bootstrap.sh rails,react-native /path/to/my-mobile-app           # API + mobile
./bootstrap.sh rails,react-nextjs /path/to/my-fullstack-app        # API + web
./bootstrap.sh rails,react-nextjs,react-native /path/to/my-app     # API + web + mobile
./bootstrap.sh python-fastapi,react-nextjs /path/to/my-python-app  # Python API + web

# Force overwrite existing .claude/ directory
./bootstrap.sh rails /path/to/my-rails-app --force

# Inspect what would be composed (use a temp directory)
./bootstrap.sh rails,react-native /tmp/test-output

# Check shared base layer
ls shared/agents/ shared/skills/ shared/hooks/

# Check stack-specific overlays
ls stacks/rails/skills/
ls stacks/react-nextjs/patterns/
```
