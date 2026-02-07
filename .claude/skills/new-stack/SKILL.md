---
name: new-stack
description: Add a new stack to the agents bootstrap system. Generates all required files (stack.yaml, agents, skills, patterns, styles) and updates documentation.
---

# /new-stack — Add New Stack

Creates a complete, fully-integrated stack for the agents bootstrap system.

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
    role: developer
    model: opus
    tools:
      - Read
      - Write
      - Edit
      - Bash
      - Grep
      - Glob

  - name: <role>-tester
    template: agents/<role>-tester.md.j2
    description: <test_framework> testing specialist
    role: tester
    model: sonnet
    tools:
      - Read
      - Write
      - Edit
      - Bash
      - Grep
      - Glob

  - name: <role>-reviewer
    template: agents/<role>-reviewer.md.j2
    description: <framework> code reviewer
    role: reviewer
    model: opus
    tools:
      - Read
      - Grep
      - Glob

skills:
  - <skill_1>
  - <skill_2>

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
  framework: <framework>
  language: <language>
  test_framework: <test_framework>
  orm: <orm>
  package_manager: <package_manager>
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

### Step 12: Report Results

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

### Files Updated
- README.md (Added to Available Stacks table)

### Verification
✓ python bootstrap.py --validate <name>
✓ python bootstrap.py --list (shows <name>)

### Next Steps
1. Review generated files and customize as needed
2. Add framework-specific code examples to patterns
3. Test: python bootstrap.py <name> /tmp/test-app
4. Commit: git add stacks/<name> && git commit -m "feat: add <name> stack"
```

---

## Key Rules

1. **Follow the schema** — stack.yaml must match `schemas/stack.schema.json`
2. **Use existing patterns** — Reference similar stacks, don't invent new structures
3. **Role determines agent prefix** — Backend uses `backend-*`, frontend uses `frontend-*`, mobile uses `mobile-*`
4. **Validate before reporting** — Always run `--validate` to catch errors
5. **Update README** — The stack should appear in documentation

---

## Reference Files

Templates are in `base/skills/new-stack/references/`:
- `stack-yaml-template.yaml` — stack.yaml structure
- `developer-agent.md.j2.txt` — Developer agent template
- `tester-agent.md.j2.txt` — Tester agent template
- `reviewer-agent.md.j2.txt` — Reviewer agent template
- `skill-template.md.txt` — Skill file template
- `patterns-template.md.txt` — Patterns file template
- `styles-template.md.txt` — Styles file template
