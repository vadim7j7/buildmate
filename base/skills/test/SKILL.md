---
name: test
description: Delegate to the stack-specific tester agent to run tests
---

# /test

## What This Does

Detects the project's test framework, delegates test execution to the stack's
tester agent, and reports a pass/fail summary. Works with any stack by
auto-detecting the available test runner.

## Usage

```
/test                     # Run the full test suite
/test path/to/file.test   # Run a specific test file
/test --coverage          # Run with coverage reporting
```

## How It Works

1. **Detect test framework.** Inspect the project for known test configuration
   files and scripts:
   - `package.json` scripts (`test`, `vitest`, `jest`) for JS/TS stacks
   - `pytest.ini`, `pyproject.toml [tool.pytest]`, `setup.cfg` for Python
   - `Gemfile` with `rspec` for Ruby (`bundle exec rspec`)
   - `go.mod` for Go (`go test ./...`)
   - `mix.exs` for Elixir (`mix test`)
   - `Cargo.toml` for Rust (`cargo test`)
   - Falls back to the stack's default test command if detection fails.

2. **Delegate to the stack's tester agent.** Use the Task tool to invoke the
   tester sub-agent with the following context:
   - Which test framework was detected
   - Which files or directories to test (all if none specified)
   - Whether coverage was requested
   - Any previous pipeline context from `.agent-pipeline/implement.md`

3. **Run the test suite.** The tester agent executes the tests, capturing
   stdout and stderr. If specific files were requested, only those files are
   run.

4. **Report results.** The tester agent returns a structured summary:

   ```
   ## Test Results

   **Status:** PASS | FAIL
   **Total:** N tests
   **Passed:** N
   **Failed:** N
   **Skipped:** N
   **Duration:** Ns

   ### Failures (if any)
   - test_name: reason
   ```

5. **Write pipeline artefact.** If running as part of a sequential pipeline,
   write results to `.agent-pipeline/test.md` for the next stage.

## Supported Frameworks

| Stack      | Frameworks                        |
|------------|-----------------------------------|
| TypeScript | Vitest, Jest, Mocha, Playwright   |
| Python     | pytest, unittest                  |
| Ruby       | RSpec, Minitest                   |
| Go         | go test                           |
| Elixir     | ExUnit, mix test                  |
| Rust       | cargo test                        |

## Error Handling

- If no test framework is detected, report an error and suggest configuring
  one.
- If tests fail, report the failures clearly but do **not** attempt to fix
  them. That is the implementer agent's responsibility.
- If the test process crashes (non-test failure), report the crash with the
  full error output.
