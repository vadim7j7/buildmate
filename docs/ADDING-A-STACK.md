# Adding a New Stack

Step-by-step guide for creating a new stack template that plugs into the agent template generator.

---

## Table of Contents

- [Overview](#overview)
- [Step-by-Step Guide](#step-by-step-guide)
  - [1. Create the Stack Directory](#1-create-the-stack-directory)
  - [2. Create CLAUDE.md](#2-create-claudemd)
  - [3. Create settings.json](#3-create-settingsjson)
  - [4. Create Agents](#4-create-agents)
  - [5. Create Skills](#5-create-skills)
  - [6. Create Code Generation Skills](#6-create-code-generation-skills)
  - [7. Create Hooks](#7-create-hooks)
  - [8. Create Patterns and Styles](#8-create-patterns-and-styles)
- [Template File Formats](#template-file-formats)
- [How the Composition Layer Works](#how-the-composition-layer-works)
- [Testing Your New Stack](#testing-your-new-stack)
- [Checklist for a Complete Stack](#checklist-for-a-complete-stack)

---

## Overview

A stack template is a directory under `stacks/` that contains agent configurations, skills, hooks, and conventions specific to a technology stack. When a user runs `./bootstrap.sh <stack> <target>`, the shared base layer is composed with the stack-specific overlay to produce the final `.claude/` configuration.

The existing stacks provide good reference implementations:
- `stacks/rails/` -- Server-side Ruby on Rails
- `stacks/react-nextjs/` -- Client-side React + Next.js
- `stacks/react-native/` -- Mobile React Native + Expo
- `stacks/fullstack/` -- Combined Rails + React

---

## Step-by-Step Guide

### 1. Create the Stack Directory

Create the directory structure under `stacks/`:

```bash
mkdir -p stacks/my-stack/{agents,skills,hooks,patterns,styles}
```

The full structure will look like:

```
stacks/my-stack/
  CLAUDE.md              # Stack-specific instructions (appended to shared CLAUDE.md)
  settings.json          # Stack-specific permissions (deep-merged with shared)
  agents/                # Agent definitions
    orchestrator.md      # Stack-specific orchestrator (replaces shared)
    my-developer.md      # Stack's developer agent
    my-tester.md         # Stack's tester agent
    my-reviewer.md       # Stack's reviewer agent
  skills/                # Stack-specific skills
    test/                # Overrides shared /test skill
      SKILL.md
      references/
    review/              # Overrides shared /review skill
      SKILL.md
      references/
    new-widget/          # Stack-only skill (added alongside shared skills)
      SKILL.md
      references/
        widget-examples.md
  hooks/                 # Hook scripts
    post-edit-format.sh  # Auto-format after edits
    post-edit-lint.sh    # Auto-lint after edits
    post-edit-test.sh    # Auto-test after edits
  patterns/              # Code pattern references
    my-patterns.md       # Patterns for this stack
  styles/                # Code style guides
    my-style-guide.md    # Style conventions for this stack
```

### 2. Create CLAUDE.md

Create `stacks/my-stack/CLAUDE.md` with stack-specific instructions. This file is concatenated after the shared CLAUDE.md during composition, so it should extend (not repeat) the shared content.

Include the following sections:

```markdown
# My Stack Agent System

This project uses a multi-agent architecture powered by Claude Code, specialised for
My Stack applications.

## Quick Start

Say **"Use PM: [task description]"** to trigger the full orchestration pipeline.

## Technology Stack

| Technology | Version / Notes |
|------------|-----------------|
| Language   | Version         |
| Framework  | Version         |
| Test Runner| Version         |

## Project Structure

\```
src/
  components/    # Description
  services/      # Description
  ...
\```

## Key Commands

| Command          | Purpose                    |
|------------------|----------------------------|
| `npm test`       | Run the test suite         |
| `npm run lint`   | Run the linter             |
| `npm run build`  | Build the project          |

## Agent Pipeline

\```
Plan --> Implement --> Test --> Review --> Eval
\```

| Stage     | Agent           | Purpose                      |
|-----------|-----------------|------------------------------|
| Plan      | PM              | Break task into sub-tasks    |
| Implement | my-developer    | Write production code        |
| Test      | my-tester       | Write and run tests          |
| Review    | my-reviewer     | Code review                  |
| Eval      | eval-agent      | Quality scoring              |

## Code Patterns

### Pattern 1: Service Pattern

\```language
// Example code showing the pattern
\```

### Pattern 2: Component Pattern

\```language
// Example code showing the pattern
\```

## Quality Gates

| Gate       | Command          | Requirement |
|------------|------------------|-------------|
| TypeScript | `npx tsc`        | Zero errors |
| Lint       | `npm run lint`   | Zero errors |
| Tests      | `npm test`       | All passing |

## Available Slash Commands

| Command        | Description                          |
|----------------|--------------------------------------|
| `/test`        | Run tests via tester agent           |
| `/review`      | Code review via reviewer agent       |
| `/new-widget`  | Generate a new widget                |

## Delegation Rules

1. Only the main agent delegates.
2. One responsibility per agent.
3. Context flows forward via `.agent-pipeline/`.
4. Failures stop the pipeline.
```

### 3. Create settings.json

Create `stacks/my-stack/settings.json` with stack-specific permissions. These are deep-merged with the shared `settings.json` during composition -- permission arrays are concatenated and deduplicated.

```json
{
  "permissions": {
    "allow": [
      "Bash(npm test:*)",
      "Bash(npm run lint:*)",
      "Bash(npm run build:*)",
      "Bash(npx tsc:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push:*)",
      "Bash(git checkout:*)",
      "Bash(gh pr create:*)"
    ]
  }
}
```

The shared `settings.json` already includes permissions for basic bash commands (ls, find, grep, cat, git status, git diff, etc.), so you only need to add stack-specific tool permissions.

### 4. Create Agents

Create agent definition files in `stacks/my-stack/agents/`. At minimum, create four agents:

#### orchestrator.md (Replaces Shared)

The orchestrator is the most important agent. It defines how the PM workflow coordinates your stack's specialist agents. Use the YAML frontmatter format:

```markdown
---
name: PM
description: |
  ORCHESTRATION GUIDE for My Stack features. When user says "Use PM:" or "/pm",
  the MAIN AGENT follows this workflow to coordinate specialist agents.
  IMPORTANT: This is NOT a sub-agent to spawn via Task tool.
tools: Read, Write, Edit, Bash, Grep, Glob, Task
model: opus
---

# PM Orchestration Workflow Guide (My Stack)

## CRITICAL: This Is NOT a Spawnable Agent

**This file is a WORKFLOW GUIDE, not a sub-agent.** The main Claude agent reads
this file and follows the instructions directly.

## Agent Mapping

| Role      | subagent_type  | Purpose                    |
|-----------|----------------|----------------------------|
| Developer | my-developer   | Write production code      |
| Tester    | my-tester      | Write and run tests        |
| Reviewer  | my-reviewer    | Review code quality        |

## Phase 1: Planning
...

## Phase 2: Implementation
...

## Phase 3: Testing
...

## Phase 4: Review
...

## Phase 5: Completion
...
```

Key points for the orchestrator:
- Clearly state that it is a workflow guide, NOT a spawnable agent
- Map roles to your stack's specific agent names
- Define quality gates specific to your stack
- Reference your stack's patterns and styles
- Include delegation templates with specific instructions for each agent

#### Developer Agent

```markdown
---
name: my-developer
description: My Stack developer. Writes production-quality code following project patterns.
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
---

# My Stack Developer Agent

You are a senior developer specializing in [technology].

## Before Writing Any Code

**ALWAYS** read the following reference files first:
1. `patterns/my-patterns.md`
2. `styles/my-style-guide.md`

## Code Patterns
...

## Style Rules
...

## Completion Checklist
...
```

#### Tester Agent

```markdown
---
name: my-tester
description: My Stack testing specialist. Writes and runs comprehensive tests.
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
---

# My Stack Tester Agent

You are a testing specialist for [technology].

## Test Patterns
...

## Coverage Targets
...

## Running Tests
...
```

#### Reviewer Agent

```markdown
---
name: my-reviewer
description: My Stack code reviewer. Reviews code against conventions and quality standards.
tools: Read, Grep, Glob, Bash
model: opus
---

# My Stack Reviewer Agent

You are a code reviewer for [technology].

## Review Checklist
...

## Severity Levels
...

## Output Format
...
```

### 5. Create Skills

Create skill directories for at minimum `/test` and `/review` (these override the shared versions with stack-specific behavior):

#### test/ (Override)

```
stacks/my-stack/skills/test/
  SKILL.md
  references/
    test-patterns.md
```

```markdown
---
name: test
description: Run tests using [test framework] via the my-tester agent
---

# /test

## What This Does

Runs [test framework] tests and reports results.

## Usage

\```
/test                    # Full suite
/test path/to/test.ts    # Specific file
/test --coverage         # With coverage
\```

## How It Works

1. Detect test configuration
2. Delegate to my-tester agent
3. Run the test suite
4. Report results
```

#### review/ (Override)

```
stacks/my-stack/skills/review/
  SKILL.md
  references/
    review-patterns.md
    security-patterns.md
```

### 6. Create Code Generation Skills

Code generation skills are the most valuable stack-specific skills. Each generates files following your stack's patterns.

Create a skill directory with a `SKILL.md` and a `references/` subdirectory:

```
stacks/my-stack/skills/new-widget/
  SKILL.md
  references/
    widget-examples.md
```

#### SKILL.md

```markdown
---
name: new-widget
description: Generate a new widget following project patterns
---

# /new-widget

## What This Does

Generates a new widget with proper structure, types, and test file.

## Usage

\```
/new-widget MyWidget
/new-widget DataTable --variant=sortable
\```

## How It Works

1. **Read reference patterns.** Load examples from:
   - `skills/new-widget/references/widget-examples.md`
   - `patterns/my-patterns.md`

2. **Determine file locations.** Based on the widget name:
   - Source: `src/widgets/<name>.ts`
   - Test: `src/widgets/__tests__/<name>.test.ts`

3. **Generate the widget.** Create the source file following the
   pattern from references.

4. **Generate the test.** Create the test file with:
   - Render test
   - Interaction tests
   - Edge case tests

5. **Run checks.** After generating:
   - `npx tsc --noEmit` (zero errors)
   - `npm run lint` (zero errors)
```

#### references/widget-examples.md

```markdown
# Widget Examples

## Basic Widget

\```typescript
// src/widgets/SimpleWidget.ts
export type SimpleWidgetProps = {
  title: string;
  children: React.ReactNode;
};

export function SimpleWidget({ title, children }: SimpleWidgetProps) {
  return (
    <div>
      <h2>{title}</h2>
      {children}
    </div>
  );
}
\```

## Widget with State

\```typescript
// src/widgets/CounterWidget.ts
'use client';

import { useState } from 'react';

export type CounterWidgetProps = {
  initialCount?: number;
};

export function CounterWidget({ initialCount = 0 }: CounterWidgetProps) {
  const [count, setCount] = useState(initialCount);
  return (
    <button onClick={() => setCount(c => c + 1)}>
      Count: {count}
    </button>
  );
}
\```
```

### 7. Create Hooks

Hooks are shell scripts that run automatically before or after certain events. Common hooks include:

#### post-edit-format.sh

```bash
#!/usr/bin/env bash
# Auto-format files after edits
set -euo pipefail

FILE="$1"
EXTENSION="${FILE##*.}"

case "$EXTENSION" in
  ts|tsx|js|jsx)
    npx prettier --write "$FILE" 2>/dev/null || true
    ;;
  rb)
    bundle exec rubocop -A "$FILE" 2>/dev/null || true
    ;;
esac
```

#### post-edit-lint.sh

```bash
#!/usr/bin/env bash
# Run linter on edited files
set -euo pipefail

FILE="$1"
npm run lint -- "$FILE" 2>/dev/null || true
```

#### post-edit-test.sh

```bash
#!/usr/bin/env bash
# Run related tests after edits
set -euo pipefail

FILE="$1"
# Find and run the corresponding test file
TEST_FILE="${FILE%.ts}.test.ts"
if [[ -f "$TEST_FILE" ]]; then
  npx jest "$TEST_FILE" --passWithNoTests 2>/dev/null || true
fi
```

### 8. Create Patterns and Styles

These directories hold reference documentation that agents read before writing code.

#### patterns/my-patterns.md

Document the code patterns used in your stack:

```markdown
# My Stack Code Patterns

## Service Pattern

Services encapsulate business logic...

\```language
// Example service
\```

## Component Pattern

Components follow...

\```language
// Example component
\```
```

#### styles/my-style-guide.md

Document the coding style conventions:

```markdown
# My Stack Style Guide

## Naming Conventions

- Files: kebab-case
- Classes: PascalCase
- Functions: camelCase

## Formatting

- Indent: 2 spaces
- Quotes: single quotes
- Semicolons: required

## Import Order

1. Standard library
2. Third-party
3. Internal
```

---

## Template File Formats

### Agent Files (YAML Frontmatter + Markdown)

```markdown
---
name: agent-name
description: Brief description of the agent's role
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
---

# Agent Title

Agent instructions in Markdown...
```

Available frontmatter fields:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Agent identifier (used in Task tool references) |
| `description` | Yes | What the agent does (shown in listings) |
| `tools` | Yes | Comma-separated list of available tools |
| `model` | No | Model to use (default: opus) |

### Skill Files (YAML Frontmatter + Markdown)

```markdown
---
name: skill-name
description: Brief description of what the skill does
---

# /skill-name

## What This Does
...

## Usage
...

## How It Works
...
```

Available frontmatter fields:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Skill identifier (used as the slash command name) |
| `description` | Yes | What the skill does |

---

## How the Composition Layer Works

Understanding how composition works helps you structure your stack correctly.

### Composition Process

When `./bootstrap.sh my-stack /path/to/project` runs:

1. **Copy shared base.** Everything from `shared/` is copied to a temporary directory as the base layer. This includes shared agents (orchestrator, eval-agent, security-auditor, regression-monitor, documentation-specialist), shared skills (delegate, parallel, sequential, test, review, eval, security, docs), shared hooks, shared `CLAUDE.md`, and shared `settings.json`.

2. **Overlay agents.** Files from `stacks/my-stack/agents/` are overlaid:
   - If `orchestrator.md` exists in both shared and stack, the stack version **replaces** the shared version
   - Stack-only agents (like `my-developer.md`) are **added** to the output

3. **Overlay skills.** Directories from `stacks/my-stack/skills/` are overlaid:
   - If `test/` exists in both, the entire stack `test/` directory **replaces** the shared one
   - Stack-only skills (like `new-widget/`) are **added**

4. **Overlay hooks.** Files from `stacks/my-stack/hooks/` are overlaid:
   - Stack hooks with the same name **replace** shared hooks
   - Stack-only hooks are **added**

5. **Copy patterns and styles.** These are copied directly from the stack -- there is no shared base for them.

6. **Merge CLAUDE.md.** Shared `CLAUDE.md` content comes first, followed by a separator and the stack `CLAUDE.md`.

7. **Merge settings.json.** Deep-merged using `jq`:
   - Permission arrays are concatenated and deduplicated
   - Object fields are recursively merged (stack wins on conflicts)
   - Scalars from stack override shared values

### What This Means for Your Stack

- **You do not need to duplicate shared content.** The shared layer provides agents like eval-agent and security-auditor, skills like /delegate and /parallel, and base permissions. Your stack only needs to add what is specific to it.
- **Override by matching the filename.** To customize how `/test` works for your stack, create `stacks/my-stack/skills/test/SKILL.md`. It will replace the shared version entirely.
- **Add by using a new filename.** To add a new skill, create `stacks/my-stack/skills/my-new-skill/SKILL.md`. It will be added alongside the shared skills.

---

## Testing Your New Stack

### Step 1: Register the Stack

Add your stack name to the `VALID_STACKS` array in `bootstrap-lib/validate.sh`:

```bash
readonly VALID_STACKS=("rails" "react-nextjs" "react-native" "fullstack" "my-stack")
```

### Step 2: Test Bootstrap

Run bootstrap against a test project:

```bash
# Create a test directory
mkdir -p /tmp/test-my-stack
cd /tmp/test-my-stack
git init

# Run bootstrap
/path/to/agents/bootstrap.sh my-stack /tmp/test-my-stack
```

### Step 3: Verify the Output

Check that everything was composed correctly:

```bash
# Check installed agents
ls /tmp/test-my-stack/.claude/agents/
# Should include: orchestrator.md, my-developer.md, my-tester.md, my-reviewer.md,
#                 eval-agent.md, security-auditor.md, regression-monitor.md,
#                 documentation-specialist.md

# Check installed skills
ls /tmp/test-my-stack/.claude/skills/
# Should include: shared skills (delegate, parallel, sequential, docs, eval, security)
#                 + your stack skills (test, review, new-widget, etc.)

# Check CLAUDE.md was merged
head -50 /tmp/test-my-stack/CLAUDE.md
# Should show shared content, then separator, then your stack content

# Check settings.json was merged
cat /tmp/test-my-stack/.claude/settings.json | jq '.permissions.allow'
# Should include both shared and stack permissions

# Check hooks
ls /tmp/test-my-stack/.claude/hooks/
# Should include your stack hooks

# Check patterns and styles
ls /tmp/test-my-stack/.claude/patterns/
ls /tmp/test-my-stack/.claude/styles/
```

### Step 4: Test with Claude Code

Open the test project in Claude Code and verify:

1. The orchestrator responds to "Use PM: ..."
2. Skills are available as slash commands
3. Agent delegation works correctly
4. Code generation skills produce correct output

### Step 5: Test with --force

```bash
/path/to/agents/bootstrap.sh my-stack /tmp/test-my-stack --force
```

Verify that the output is clean (no duplicates or stale files).

---

## Checklist for a Complete Stack

Use this checklist to ensure your stack template is complete:

### Required Files

- [ ] `stacks/my-stack/CLAUDE.md` -- Stack-specific instructions with:
  - [ ] Technology stack table
  - [ ] Project structure
  - [ ] Key commands
  - [ ] Agent pipeline
  - [ ] Code patterns with examples
  - [ ] Quality gates
  - [ ] Available slash commands
  - [ ] Delegation rules

- [ ] `stacks/my-stack/settings.json` -- Stack-specific permissions

- [ ] `stacks/my-stack/agents/orchestrator.md` -- Orchestrator with:
  - [ ] "NOT a spawnable agent" warning
  - [ ] Agent mapping table
  - [ ] Planning phase
  - [ ] Implementation phase with delegation templates
  - [ ] Testing phase
  - [ ] Review phase
  - [ ] Completion phase with checklist

- [ ] `stacks/my-stack/agents/<developer>.md` -- Developer agent with:
  - [ ] Technology expertise
  - [ ] "Read patterns first" instruction
  - [ ] Code patterns with examples
  - [ ] Style rules
  - [ ] Completion checklist (lint, test commands)

- [ ] `stacks/my-stack/agents/<tester>.md` -- Tester agent with:
  - [ ] Test framework expertise
  - [ ] Test patterns with examples
  - [ ] Coverage targets
  - [ ] Test running instructions

- [ ] `stacks/my-stack/agents/<reviewer>.md` -- Reviewer agent with:
  - [ ] Review checklist
  - [ ] Severity levels (blocker, warning, suggestion)
  - [ ] Output format
  - [ ] Review principles

### Required Skills (Override Shared)

- [ ] `stacks/my-stack/skills/test/SKILL.md` -- Stack-specific test execution
- [ ] `stacks/my-stack/skills/review/SKILL.md` -- Stack-specific code review

### Recommended Skills (Stack-Specific)

- [ ] At least one code generation skill (e.g., `/new-component`, `/new-service`)
- [ ] Each code generation skill has a `references/` directory with examples

### Optional Files

- [ ] `stacks/my-stack/hooks/post-edit-format.sh` -- Auto-format hook
- [ ] `stacks/my-stack/hooks/post-edit-lint.sh` -- Auto-lint hook
- [ ] `stacks/my-stack/hooks/post-edit-test.sh` -- Auto-test hook
- [ ] `stacks/my-stack/hooks/post-edit-typecheck.sh` -- Auto-typecheck hook
- [ ] `stacks/my-stack/patterns/<name>.md` -- Code pattern references
- [ ] `stacks/my-stack/styles/<name>.md` -- Style guide references

### Registration

- [ ] Stack name added to `VALID_STACKS` in `bootstrap-lib/validate.sh`
- [ ] Bootstrap tested with `./bootstrap.sh my-stack /path/to/test`
- [ ] Bootstrap tested with `--force` flag
- [ ] Output verified (agents, skills, hooks, patterns, styles, CLAUDE.md, settings.json)
- [ ] Tested with Claude Code (PM workflow, skills, delegation)

---

## Related Documentation

- [BOOTSTRAP.md](BOOTSTRAP.md) -- How to use bootstrap.sh
- [AGENTS.md](AGENTS.md) -- Agent roles and delegation patterns
- [SKILLS.md](SKILLS.md) -- Skill descriptions and usage
- [EVALS.md](EVALS.md) -- How to run quality evaluations
