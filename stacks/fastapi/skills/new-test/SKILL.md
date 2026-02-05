---
name: new-test
description: Generate a pytest test file for a FastAPI module
---

# /new-test

## What This Does

Generates a pytest test file for a specified module (router, service, or schema) with
appropriate fixtures, async test methods, and standard test structure.

## Usage

```
/new-test routers/projects       # Creates tests/routers/test_projects.py
/new-test services/project       # Creates tests/services/test_project_service.py
/new-test schemas/project        # Creates tests/schemas/test_project.py
/new-test tasks/sync             # Creates tests/tasks/test_sync.py
```

## How It Works

1. **Read reference patterns.** Load the test pattern from:
   - `skills/new-test/references/test-examples.md`
   - `skills/test/references/pytest-patterns.md`
   - `patterns/backend-patterns.md`

2. **Determine test target.** Parse the argument to determine what to test:
   - `routers/projects` generates HTTP integration tests using `AsyncClient`
   - `services/project` generates unit tests with `AsyncSession` fixture
   - `schemas/project` generates validation tests
   - `tasks/sync` generates Celery task tests

3. **Read the source module.** Read the corresponding source file to understand the
   API surface: functions, methods, parameters, return types.

4. **Generate the test file.** Create the test module with:
   - `from __future__ import annotations`
   - Appropriate imports and fixtures
   - Test class with descriptive name
   - Test methods for happy path, edge cases, error conditions
   - Type annotations on all test methods

5. **Run quality checks.**

   ```bash
   uv run ruff format <test_file>
   uv run ruff check <test_file>
   uv run pytest <test_file> -v
   ```

6. **Report results.** Show the generated file and test results.

## Generated Files

```
tests/<layer>/test_<module>.py
```
