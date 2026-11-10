---
name: new-stack
description: Add a new stack to Buildmate. Generates all required files (stack.yaml, agents, skills, patterns, styles) and updates documentation.
---

# /new-stack — Add New Stack

Creates a complete, fully-integrated stack for Buildmate.

## Usage

```
/new-stack django
/new-stack laravel
/new-stack flutter
```

## What Gets Created

```
stacks/<name>/
├── stack.yaml              # Stack configuration
├── agents/
│   ├── <role>-developer.md.j2
│   ├── <role>-tester.md.j2
│   └── <role>-reviewer.md.j2
├── skills/                 # Stack-specific skills
├── patterns/
│   └── <role>-patterns.md
└── styles/
    └── <role>-<language>.md
```

## What Gets Updated

- `README.md` — Adds stack to "Available Stacks" table
- `tests/` — Adds tests for the new stack
- `CLAUDE.md` — Updates if stack list mentioned

## What May Need Updates (Check Case-by-Case)

- `schemas/stack.schema.json` — If new options/fields are needed
- `base/` — If stack requires new shared agents or skills
- `lib/config.py` — If stack has special loading requirements

## What Auto-Works (No Changes Needed)

- `python bootstrap.py --list` — Auto-discovers stacks/
- `python bootstrap.py --validate <name>` — Works if schema valid
- `python bootstrap.py <name> /path` — Works if stack valid

---

## Workflow

### Step 1: Gather Stack Information

Use **AskUserQuestion** to collect details:

**Question 1: Stack Type**
```
What type of stack is this?
- Backend API (like rails, fastapi, django)
- Frontend (like nextjs)
- Mobile (like react-native)
- Other
```

**Question 2: Basic Info**
Based on the stack name provided, ask:
```
Stack Details:
- Display Name: (e.g., "Django REST API")
- Description: (e.g., "Backend API with Django and DRF")
- Language: (e.g., "Python")
- Framework: (e.g., "Django 5+ with Django REST Framework")
```

**Question 3: Quality Gates**
```
Quality Gate Commands:
- Lint command: (e.g., "ruff check .")
- Lint fix command: (e.g., "ruff check . --fix")
- Test command: (e.g., "pytest")
- Typecheck command (optional): (e.g., "mypy .")
```

**Question 4: Variables**
```
Template Variables:
- Test framework: (e.g., "pytest-django")
- ORM: (e.g., "Django ORM")
- Package manager: (e.g., "uv", "pip", "poetry")
```

**Question 5: Compatible Stacks**
```
Which stacks can be combined with this one?
☑ nextjs
☑ react-native
☐ rails (same backend role - conflict)
☐ fastapi (same backend role - conflict)
```

**Question 6: Skills to Generate**
```
Which skills should be created?
☑ new-model
☑ new-view / new-router / new-controller
☑ new-serializer / new-schema
☑ db-migrate
☑ new-test
```

**Question 7: Profile (Optional)**
```
Create a profile for this stack?
- Yes, create <name>-api profile
- No, just the stack
```

---

### Step 2: Analyze Reference Stacks

Based on stack type, read similar stacks:

| Stack Type | Read These |
|------------|------------|
| Backend API | `stacks/rails/stack.yaml`, `stacks/fastapi/stack.yaml` |
| Frontend | `stacks/nextjs/stack.yaml` |
| Mobile | `stacks/react-native/stack.yaml` |

Also read:
- `schemas/stack.schema.json` — Validation rules
- Reference templates in `base/skills/new-stack/references/`

---

### Step 3: Generate stack.yaml

Create `stacks/<name>/stack.yaml`:

```yaml
name: <name>
display_name: <display_name>
description: <description>

default_model: opus

compatible_with:
  - <compatible_stack_1>
  - <compatible_stack_2>

agents:
  - name: <role>-developer
    template: agents/<role>-developer.md.j2
    description: Senior <framework> developer
    model: opus
    tools:
      - Read
      - Write
      - Edit
      - Bash
      - Grep
      - Glob
    skills:
      - <skill_1>
      - <skill_2>

  - name: <role>-tester
    template: agents/<role>-tester.md.j2
    description: <test_framework> testing specialist
    model: sonnet
    tools:
      - Read
      - Write
      - Edit
      - Bash
      - Grep
      - Glob
    skills:
      - test                 # REQUIRED: must always be here

  - name: <role>-reviewer
    template: agents/<role>-reviewer.md.j2
    description: <framework> code reviewer
    model: opus
    tools:
      - Read
      - Grep
      - Glob
      - Bash

# Top-level skills: MUST include every agent-level skill + test
skills:
  - <skill_1>
  - <skill_2>
  - test                     # REQUIRED: matches tester agent

quality_gates:
  lint:
    command: <lint_command>
    fix_command: <lint_fix_command>
    description: <language> linting
  tests:
    command: <test_command>
    description: <test_framework> test suite

patterns:
  - patterns/<role>-patterns.md

styles:
  - styles/<role>-<language>.md

variables:
  framework: <framework>     # REQUIRED
  language: <language>        # REQUIRED (or inherited from parent)
  test_framework: <test_fw>  # REQUIRED
  dev_port: <port>           # REQUIRED
  orm: <orm>
  package_manager: <pkg_mgr>

setup:
  install_command: <install_cmd>  # REQUIRED — e.g., "bundle install", "uv sync"
  # post_install:                 # Optional — e.g., database setup
  #   - "<post_install_cmd>"
  dev_server_check: <check_cmd>   # Optional — e.g., "ruby -v && bundle -v"

verification:
  enabled: true
  auto_verify: true
  max_retries: 3
  dev_server:
    command: <start_command>  # e.g., "bundle exec rails server"
    port: <port>             # MUST match variables.dev_port
    health_check: /health    # Standardized for all backend stacks
```

---

### Step 4: Generate Agent Templates

Create agent templates in `stacks/<name>/agents/`:

**Developer Agent** — `<role>-developer.md.j2`

Read the reference template at `base/skills/new-stack/references/developer-agent.md.j2.txt`
and customize for the new stack.

**Tester Agent** — `<role>-tester.md.j2`

Read the reference template at `base/skills/new-stack/references/tester-agent.md.j2.txt`
and customize for the new stack.

**Reviewer Agent** — `<role>-reviewer.md.j2`

Read the reference template at `base/skills/new-stack/references/reviewer-agent.md.j2.txt`
and customize for the new stack.

---

### Step 5: Generate Skills

For each skill selected, create `stacks/<name>/skills/<skill>/SKILL.md`.

Read reference template at `base/skills/new-stack/references/skill-template.md.txt`
and customize for each skill.

Common skills by stack type:

| Backend | Frontend | Mobile |
|---------|----------|--------|
| new-model | new-component | new-screen |
| new-controller/view | new-page | new-store |
| new-service | new-container | new-query |
| new-serializer/schema | new-form | new-db-query |
| db-migrate | new-api-service | platform-check |

---

### Step 6: Generate Patterns File

Create `stacks/<name>/patterns/<role>-patterns.md`:

Read reference template at `base/skills/new-stack/references/patterns-template.md.txt`
and customize with framework-specific patterns:

- Model/Entity pattern
- Controller/View/Router pattern
- Service pattern
- Repository pattern (if applicable)
- Test patterns

---

### Step 7: Generate Styles File

Create `stacks/<name>/styles/<role>-<language>.md`:

Read reference template at `base/skills/new-stack/references/styles-template.md.txt`
and customize with:

- Code style rules (naming, formatting)
- Import organization
- Type annotation rules
- Documentation standards
- Framework-specific conventions

---

### Step 8: Update README.md

Edit `README.md` and add a row to the "Available Stacks" table:

Find this section:
```markdown
## Available Stacks

| Stack | Description | Agents | Key Skills |
|-------|-------------|--------|------------|
```

Add a new row:
```markdown
| `<name>` | <display_name> | <role>-developer, <role>-tester, <role>-reviewer | <skill_1>, <skill_2>, ... |
```

---

### Step 9: Create Profile (Optional)

If user requested a profile, create `profiles/<name>-api.yaml`:

```yaml
name: <name>-api
description: <description>
stacks:
  - <name>
options: {}
```

---

### Step 10: Validate

Run validation:

```bash
source .venv/bin/activate
python bootstrap.py --validate <name>
```

If validation fails:
1. Read the error message
2. Fix the issue in stack.yaml or agent templates
3. Re-validate

---

### Step 11: Test Bootstrap

Run a dry-run test:

```bash
python bootstrap.py <name> /tmp/test-<name> --dry-run
```

Verify the output structure looks correct.

---

### Step 12: Add Tests

Create tests for the new stack in `tests/`:

**12.1 Check existing test patterns:**

```bash
cat tests/test_config.py     # Stack loading tests
cat tests/test_renderer.py   # Rendering tests
cat tests/test_integration.py # Bootstrap tests
```

**12.2 Add stack to existing test cases:**

Edit `tests/test_integration.py` and add:

```python
def test_bootstrap_<name>(self, tmp_path):
    """Test bootstrapping <name> stack."""
    result = subprocess.run(
        ["python", "bootstrap.py", "<name>", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (tmp_path / ".claude").exists()
    assert (tmp_path / ".claude" / "agents").exists()
```

Edit `tests/test_config.py` and add:

```python
def test_load_<name>_stack(self):
    """Test loading <name> stack configuration."""
    stack = load_stack("<name>")
    assert stack.name == "<name>"
    assert len(stack.agents) >= 3  # developer, tester, reviewer
```

**12.3 Run tests:**

```bash
source .venv/bin/activate
python -m pytest tests/ -v -k "<name>"
python -m pytest tests/ -v  # Run all tests
```

---

### Step 13: Check Schema Updates (If Needed)

If the stack introduces new options or fields:

**13.1 Read current schema:**

```bash
cat schemas/stack.schema.json
```

**13.2 Add new option (if needed):**

If stack has configurable options (like `--db=postgresql`), add to stack.yaml:

```yaml
options:
  db:
    description: Database backend
    choices: [postgresql, mysql, sqlite]
    default: postgresql
    patterns:
      postgresql: patterns/postgresql.md
      mysql: patterns/mysql.md
```

**13.3 Validate schema still works:**

```bash
python bootstrap.py --validate <name>
```

---

### Step 14: Check Base Updates (If Needed)

If stack requires shared functionality:

**14.1 New base skill needed?**

If multiple stacks would benefit from a skill, add to `base/skills/` instead of `stacks/<name>/skills/`.

**14.2 New base agent needed?**

Rarely needed, but if so, add to `base/agents/`.

**14.3 Update renderer/config (if needed)?**

If stack has special requirements, may need updates to:
- `lib/config.py` — Stack loading
- `lib/renderer.py` — Template rendering

---

### Step 15: Update CLAUDE.md (If Needed)

Check if `CLAUDE.md` mentions available stacks:

```bash
grep -n "stacks" CLAUDE.md
grep -n "rails\|fastapi\|nextjs" CLAUDE.md
```

If it lists stacks, add the new one.

---

### Step 16: Report Results

Present a summary:

```markdown
## Stack Created: <name>

### Files Created
- stacks/<name>/stack.yaml
- stacks/<name>/agents/<role>-developer.md.j2
- stacks/<name>/agents/<role>-tester.md.j2
- stacks/<name>/agents/<role>-reviewer.md.j2
- stacks/<name>/skills/<skill_1>/SKILL.md
- stacks/<name>/skills/<skill_2>/SKILL.md
- stacks/<name>/patterns/<role>-patterns.md
- stacks/<name>/styles/<role>-<language>.md
- profiles/<name>-api.yaml (if requested)

### Files Updated
- README.md (Added to Available Stacks table)
- tests/test_config.py (Added load test)
- tests/test_integration.py (Added bootstrap test)
- CLAUDE.md (if stack list mentioned)

### Files Checked (No Changes Needed)
- schemas/stack.schema.json (existing schema sufficient)
- base/ (no new shared components needed)
- lib/ (no special handling needed)

### Verification
✓ python bootstrap.py --validate <name>
✓ python bootstrap.py --list (shows <name>)
✓ python -m pytest tests/ -v (all tests pass)
✓ python bootstrap.py <name> /tmp/test --dry-run (output correct)

### Next Steps
1. Review generated files and customize as needed
2. Add framework-specific code examples to patterns
3. Full test: python bootstrap.py <name> /tmp/test-app
4. Commit: git add stacks/<name> tests/ README.md && git commit -m "feat: add <name> stack"
```

---

## Key Rules

1. **Follow the schema** — stack.yaml must match `schemas/stack.schema.json`
2. **Use existing patterns** — Reference similar stacks, don't invent new structures
3. **Role determines agent prefix** — Backend uses `backend-*`, frontend uses `frontend-*`, mobile uses `mobile-*`
4. **Validate before reporting** — Always run `--validate` to catch errors
5. **Update README** — The stack should appear in documentation
6. **Never skip the consistency checklist** — Run through every item in the checklist below before declaring the stack complete

---

## Mandatory Consistency Checklist

**Do NOT skip any item.** Run through this entire checklist before reporting the stack as complete. This prevents the gaps that require expensive multi-session audits to fix later.

### Agents

- [ ] Stack defines exactly 3 agents: **developer**, **tester**, **reviewer**
- [ ] Each agent has its **own framework-specific `.md.j2` template** in `stacks/<name>/agents/` — never rely on generic parent templates for child stacks
- [ ] Agent names follow role convention: `backend-*` (API stacks), `frontend-*` (web UI), `mobile-*` (mobile), `scraper-*` (scraping)
- [ ] Developer model: `opus`; Tester model: `sonnet` or `opus`; Reviewer model: `opus`
- [ ] Developer + tester tools: `[Read, Write, Edit, Bash, Grep, Glob]`; Reviewer tools: `[Read, Grep, Glob, Bash]`
- [ ] Every skill listed in any agent's `skills:` array also appears in the top-level `skills:` array

### Skills

- [ ] Every top-level skill has a `SKILL.md` file — in `stacks/<name>/skills/<skill>/SKILL.md`, the parent's skills, or `base/skills/<skill>/SKILL.md`
- [ ] The `test` skill is in **both** the tester agent's skills AND the top-level skills list
- [ ] No orphaned skill directories on disk (folder exists but not in stack.yaml)
- [ ] Agent-level skills are a **subset** of top-level skills (top-level can have extras the agent doesn't list)

### Variables (minimum required)

- [ ] `framework` — name + version (e.g., `Rails 7+`, `Gin`, `Phoenix 1.7+`)
- [ ] `dev_port` — development server port number
- [ ] `test_framework` — test runner (e.g., `RSpec`, `pytest`, `Vitest`, `ExUnit`)
- [ ] `language` — inherited from parent is OK, but verify parent actually defines it
- [ ] Parent stacks must also define: `orm`, `database`, `linter`, `package_manager`

### Verification Block

- [ ] Every framework child and standalone stack has a `verification:` block
- [ ] Contains `enabled: true`, `auto_verify: true`, `max_retries: 3`
- [ ] `dev_server.command` is set to the correct start command
- [ ] `dev_server.port` matches `variables.dev_port`
- [ ] Backend stacks use `health_check: /health` (standardized — never `/api/health`, `/docs`, or `/`)
- [ ] Frontend stacks may omit `health_check` but must have `command` and `port`
- [ ] Parent language stacks (ruby, python, go, javascript, elixir) do NOT need verification

### Setup Block

- [ ] Every parent stack and standalone stack has a `setup:` block with at least `install_command`
- [ ] Child stacks that need `post_install` (e.g., database setup) define their own `setup:` block
- [ ] Child stacks without `post_install` inherit setup from parent (no `setup:` in their stack.yaml)
- [ ] `install_command` matches the stack's package manager
- [ ] `dev_server_check` (optional) verifies the dev environment

### Quality Gates

- [ ] Parent stacks define `quality_gates` with at least `lint` and `tests`
- [ ] Child stacks inherit parent gates — only override if using a different tool
- [ ] If overriding, don't accidentally drop parent gates (e.g., overriding with only `tests` loses `lint` and `typecheck`)

### Patterns and Styles

- [ ] Every file in `patterns:` and `styles:` arrays exists on disk at `stacks/<name>/<path>`
- [ ] No orphaned pattern/style files on disk that aren't referenced
- [ ] Option-referenced patterns (e.g., MongoDB in `options.db.mongodb.patterns`) must exist on disk
- [ ] Option-referenced styles must exist on disk

### Compatible With

- [ ] Backend stacks list: `[nextjs, nuxt, react-native, scraping]`
- [ ] Frontend stacks list all backend stacks they work with
- [ ] Stacks of the same role (e.g., two backends) do NOT list each other

### Options (if applicable)

- [ ] Option-referenced `patterns`, `styles`, `skills`, `quality_gates` all point to existing files/skills
- [ ] Option-injected skills have `SKILL.md` files
- [ ] Option quality_gates don't silently replace all parent gates

### Final

- [ ] `buildmate --validate <name>` passes
- [ ] All tests pass: `.venv/bin/python -m pytest tests/ -v`
- [ ] `buildmate <name> /tmp/test --dry-run` produces correct output
- [ ] Compare side-by-side with a sibling stack to verify nothing was missed

---

## Reference Files

Templates are in `base/skills/new-stack/references/`:
- `stack-yaml-template.yaml` — stack.yaml structure (includes verification block)
- `developer-agent.md.j2.txt` — Developer agent template
- `tester-agent.md.j2.txt` — Tester agent template
- `reviewer-agent.md.j2.txt` — Reviewer agent template
- `skill-template.md.txt` — Skill file template
- `patterns-template.md.txt` — Patterns file template
- `styles-template.md.txt` — Styles file template
