---
name: new-test
description: Generate a pytest test file for a Django module
---

# /new-test

## What This Does

Generates a pytest test file for a specified Django module (model, view, serializer,
or service) with appropriate fixtures, test client usage, and standard test structure.

## Usage

```
/new-test models/Article           # Creates tests for Article model
/new-test views/ArticleViewSet     # Creates tests for ArticleViewSet
/new-test serializers/Article      # Creates tests for Article serializers
/new-test services/article_publish # Creates tests for ArticlePublishService
```

## How It Works

1. **Read reference patterns.** Load the test pattern from:
   - `patterns/django-patterns.md`

2. **Determine test target.** Parse the argument to determine what to test:
   - `models/Article` generates model validation and queryset tests
   - `views/ArticleViewSet` generates API integration tests using DRF's `APIClient`
   - `serializers/Article` generates serializer validation tests
   - `services/article_publish` generates service unit tests

3. **Read the source module.** Read the corresponding source file to understand the
   API surface: fields, methods, endpoints, validation rules.

4. **Generate the test file.** Create the test module with:
   - `import pytest` and `pytestmark = pytest.mark.django_db`
   - Factory fixtures using `pytest-factoryboy` or `model_bakery`
   - `APIClient` for view tests
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
<app>/tests/test_<module>.py
```
