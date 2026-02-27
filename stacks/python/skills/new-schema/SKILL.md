---
name: new-schema
description: Generate a Pydantic or serializer schema set
---

# /new-schema

## What This Does

Generates validation/serialization schemas for a model. Uses Pydantic, Marshmallow,
or DRF serializers depending on the framework. This is the generic Python version —
framework children (Django, Flask, FastAPI) override with their own conventions.

## Usage

```
/new-schema Article              # Creates schemas for Article model
/new-schema UserProfile          # Creates schemas for UserProfile model
```

## How It Works

1. **Read reference patterns.** Load the schema pattern from:
   - `styles/backend-python.md`

2. **Detect the schema library.** Check for:
   - `pydantic` → Pydantic models (Create, Update, Response variants)
   - `marshmallow` → Marshmallow schemas
   - `djangorestframework` → DRF serializers
   - Otherwise → Pydantic by default

3. **Generate the schema file.** Create schemas with:
   - Base schema with shared fields
   - `CreateSchema` with required fields for creation
   - `UpdateSchema` with optional fields for partial updates
   - `ResponseSchema` with all fields including read-only
   - Type annotations and validators

4. **Run quality checks.**

   ```bash
   uv run ruff format <generated_files>
   uv run ruff check <generated_files>
   ```

## Generated Files

```
<module>/schemas/<name>.py  (or serializers.py for DRF)
```
