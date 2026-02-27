---
name: new-test
description: Generate a pytest test file for a Python module
---

# /new-test

## What This Does

Generates a pytest test file for a specified module (model, view, service, or utility)
with appropriate fixtures, test structure, and assertions. This is the generic Python
version — framework children (Django, Flask, FastAPI) override with their own conventions.

## Usage

```
/new-test models/Article           # Creates tests for Article model
/new-test services/article_publish # Creates tests for ArticlePublishService
/new-test utils/string_formatter   # Creates tests for string_formatter module
```

## How It Works

1. **Read reference patterns.** Load the test pattern from:
   - `styles/backend-python.md`

2. **Determine test target.** Parse the argument to determine what to test:
   - `models/Article` generates model tests
   - `services/article_publish` generates service unit tests
   - Other paths generate general unit tests

3. **Read the source module.** Read the corresponding source file to understand
   the API surface: classes, functions, methods, parameters.

4. **Generate the test file.** Create the test module with:
   - `import pytest`
   - Fixtures for common setup
   - Test classes with descriptive names
   - Tests for happy path, edge cases, error conditions
   - Parametrized tests where appropriate

5. **Run quality checks.**

   ```bash
   uv run ruff format <test_file>
   uv run ruff check <test_file>
   uv run pytest <test_file> -v
   ```

## Generated Files

```
tests/test_<module>.py
```
