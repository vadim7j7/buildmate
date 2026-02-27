---
name: new-model
description: Generate a Python data model with validation and test
---

# /new-model

## What This Does

Generates a Python data model using the project's ORM or data library (SQLAlchemy,
Django ORM, Pydantic, dataclasses). This is the generic Python version — framework
children (Django, Flask, FastAPI) override with their own conventions.

## Usage

```
/new-model Article                  # Creates Article model
/new-model UserProfile              # Creates UserProfile model
```

## How It Works

1. **Read reference patterns.** Load the model pattern from:
   - `styles/backend-python.md`

2. **Detect the project's ORM.** Check for:
   - `sqlalchemy` in dependencies → SQLAlchemy model
   - `django` in dependencies → Django ORM model
   - Otherwise → Pydantic or dataclass model

3. **Generate the model file.** Create the model with:
   - Type annotations on all fields
   - Docstrings
   - Validation constraints
   - Relationships/associations if applicable
   - `__repr__` and `__str__` methods

4. **Generate the test file.** Create tests with:
   - Model creation tests
   - Validation tests
   - Relationship tests (if applicable)

5. **Run quality checks.**

   ```bash
   uv run ruff format <generated_files>
   uv run ruff check <generated_files>
   uv run pytest <test_file> -v
   ```

## Generated Files

```
<module>/models/<model_name>.py  (or models.py updated)
tests/test_<model_name>.py
```
