---
name: test
description: Run RSpec tests via the backend-tester agent
---

# /test

## What This Does

Delegates test execution to the `backend-tester` agent, which runs RSpec for specific
files or the full test suite and reports a structured pass/fail summary.

## Usage

```
/test                              # Run the full test suite
/test spec/models/profile_spec.rb  # Run a specific spec file
/test spec/services/               # Run all specs in a directory
/test --coverage                   # Run with SimpleCov coverage report
```

## How It Works

1. **Determine scope.** If a file or directory path is provided, scope the test run
   to that path. If no argument is given, run the full suite with `bundle exec rspec`.

2. **Delegate to backend-tester.** Use the Task tool to invoke the `backend-tester`
   sub-agent with the following context:
   - Which spec files or directories to run
   - Whether coverage was requested
   - Any previous pipeline context from `.agent-pipeline/implement.md`
   - Reference files: `skills/test/references/rspec-patterns.md` and
     `skills/test/references/factory-patterns.md`

3. **Run RSpec.** The backend-tester agent executes:

   ```bash
   # Specific file
   bundle exec rspec spec/path/to/spec_file.rb --format documentation

   # Full suite
   bundle exec rspec --format progress

   # With coverage
   COVERAGE=true bundle exec rspec
   ```

4. **Report results.** The backend-tester returns a structured summary:

   ```markdown
   ## Test Results

   **Status:** PASS | FAIL
   **Total:** N examples
   **Passed:** N
   **Failed:** N
   **Pending:** N
   **Duration:** N seconds

   ### Failures (if any)
   - spec/path/file_spec.rb:42 - expected X but got Y

   ### Coverage (if requested)
   - Models: 96.2%
   - Services: 94.8%
   - Controllers: 91.5%
   ```

5. **Write pipeline artifact.** If running as part of a sequential pipeline, write
   results to `.agent-pipeline/test.md` for the next stage.

## Error Handling

- If `bundle exec rspec` is not available, check that the `rspec-rails` gem is in
  the Gemfile and run `bundle install`.
- If tests fail, report the failures clearly with file paths and line numbers. Do
  NOT attempt to fix failures; that is the backend-developer's responsibility.
- If factories are missing, the backend-tester will create them in `spec/factories/`.
- If the test process crashes (non-test failure), report the full error output.
