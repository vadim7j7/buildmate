---
name: new-model
description: Generate a Flask-SQLAlchemy model with relationships and migration
---

# /new-model

## What This Does

Generates a Flask-SQLAlchemy model with proper column definitions, relationships,
and an Alembic migration. Also generates a basic test file.

## Usage

```
/new-model Article                  # Creates Article model
/new-model UserProfile              # Creates UserProfile model
/new-model OrderItem                # Creates OrderItem model
```

## How It Works

1. **Read reference patterns.** Load the model pattern from:
   - `patterns/flask-patterns.md`
   - `styles/backend-python.md`

2. **Determine the model name and attributes.** Parse the argument and ask for
   or infer attributes based on the model name and context.

3. **Generate the model file.** Create or update `models.py` (or `models/<name>.py`) with:
   - Import from `app.extensions import db`
   - Class inheriting from `db.Model`
   - `__tablename__` explicit table name
   - Column definitions with types, nullable, defaults
   - Relationships (`db.relationship`, `back_populates`)
   - `__repr__` method
   - Standard `id`, `created_at`, `updated_at` columns
   - Docstring on the class

4. **Generate the migration.**

   ```bash
   uv run flask db migrate -m "create <table_name> table"
   ```

5. **Generate the test file.** Create tests with:
   - Model creation tests
   - Validation tests
   - Relationship tests

6. **Run quality checks.**

   ```bash
   uv run flask db upgrade
   uv run ruff format <generated_files>
   uv run ruff check <generated_files>
   uv run pytest <test_file> -v
   ```

## Generated Files

```
app/models/<resource>.py  (or app/models.py updated)
migrations/versions/<timestamp>_create_<table>.py
tests/test_models.py  (created or updated)
```
