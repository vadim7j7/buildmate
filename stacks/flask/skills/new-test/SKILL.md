---
name: new-test
description: Generate a pytest test file for a Flask module
---

# /new-test

## What This Does

Generates a pytest test file for a specified Flask module (model, route, schema,
or service) with appropriate fixtures, Flask test client, and standard test structure.

## Usage

```
/new-test models/Article           # Creates tests for Article model
/new-test routes/articles          # Creates tests for articles blueprint routes
/new-test schemas/Article          # Creates tests for Article schemas
/new-test services/article_publish # Creates tests for ArticlePublishService
```

## How It Works

1. **Read reference patterns.** Load the test pattern from:
   - `patterns/flask-patterns.md`

2. **Determine test target.** Parse the argument to determine what to test:
   - `models/Article` generates model validation and query tests
   - `routes/articles` generates integration tests using Flask test client
   - `schemas/Article` generates schema validation tests
   - `services/article_publish` generates service unit tests

3. **Read the source module.** Read the corresponding source file to understand the
   API surface.

4. **Generate the test file.** Create the test module with:
   - `import pytest`
   - Flask app and client fixtures via `conftest.py`
   - Test database fixture with rollback
   - Test classes with descriptive names
   - Tests for happy path, edge cases, error conditions

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
