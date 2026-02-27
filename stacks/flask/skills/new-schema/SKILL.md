---
name: new-schema
description: Generate a Marshmallow or Pydantic schema set
---

# /new-schema

## What This Does

Generates serialization schemas for a model with standard variants for
input validation and output formatting.

## Usage

```
/new-schema Article              # Creates schemas for Article model
/new-schema UserProfile          # Creates schemas for UserProfile model
```

## How It Works

1. **Read reference patterns.** Load the schema pattern from:
   - `patterns/flask-patterns.md`
   - `styles/backend-python.md`

2. **Determine resource name.** Parse the argument to determine the schema names:
   - `Article` becomes `ArticleSchema`, `ArticleCreateSchema`, `ArticleUpdateSchema`

3. **Generate the schema file.** Create the schema module with:
   - Base schema with shared fields
   - Create schema with required input fields
   - Update schema with optional fields for partial updates
   - Proper field types and validation
   - `Meta` class with `model` reference (if using Marshmallow-SQLAlchemy)
   - Custom validators (`@validates`, `@pre_load`)

4. **Run quality checks.**

   ```bash
   uv run ruff format <generated_files>
   uv run ruff check <generated_files>
   ```

## Generated Files

```
app/schemas/<resource>.py
```
