---
name: test
description: Run pytest tests via the backend-tester agent
---

# /test

## What This Does

Delegates test execution to the `backend-tester` agent, which runs pytest for specific
files or the full test suite and reports a structured pass/fail summary.

## Usage

```
/test                                # Run the full test suite
/test tests/routers/test_projects.py # Run a specific test file
/test tests/services/                # Run all tests in a directory
/test --coverage                     # Run with coverage report
```

## How It Works

1. **Determine scope.** If a file or directory path is provided, scope the test run
   to that path. If no argument is given, run the full suite with `uv run pytest`.

2. **Delegate to backend-tester.** Use the Task tool to invoke the `backend-tester`
   sub-agent with the following context:
   - Which test files or directories to run
   - Whether coverage was requested
   - Any previous pipeline context from `.agent-pipeline/implement.md`
   - Reference files: `skills/test/references/pytest-patterns.md`

3. **Run pytest.** The backend-tester agent executes:

   ```bash
   # Specific file
   uv run pytest tests/path/to/test_file.py -v

   # Full suite
   uv run pytest

   # With coverage
   uv run pytest --cov=app --cov-report=term-missing
   ```

4. **Report results.** The backend-tester returns a structured summary:

   ```markdown
   ## Test Results

   **Status:** PASS | FAIL
   **Total:** N tests
   **Passed:** N
   **Failed:** N
   **Skipped:** N
   **Duration:** N seconds

   ### Failures (if any)
   - tests/path/test_file.py::TestClass::test_method - AssertionError: ...

   ### Coverage (if requested)
   - Routers: 92.3%
   - Services: 96.1%
   - Models: 94.5%
   ```

5. **Write pipeline artifact.** If running as part of a sequential pipeline, write
   results to `.agent-pipeline/test.md` for the next stage.

## Error Handling

- If `uv run pytest` is not available, check that pytest is in `pyproject.toml`
  and run `uv sync`.
- If tests fail, report the failures clearly with file paths and line numbers. Do
  NOT attempt to fix failures; that is the backend-developer's responsibility.
- If conftest fixtures are missing, the backend-tester will create them.
- If the test process crashes (non-test failure), report the full error output.
