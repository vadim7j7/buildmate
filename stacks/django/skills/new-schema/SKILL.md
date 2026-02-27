---
name: new-schema
description: Generate a DRF serializer set (Base, Create, Update, Detail)
---

# /new-schema

## What This Does

Generates Django REST Framework serializers for a model with standard variants:
List, Detail, Create, and Update serializers.

## Usage

```
/new-schema Article              # Creates serializers for Article model
/new-schema UserProfile          # Creates serializers for UserProfile model
/new-schema OrderItem            # Creates serializers for OrderItem model
```

## How It Works

1. **Read reference patterns.** Load the serializer pattern from:
   - `patterns/django-patterns.md`
   - `styles/backend-python.md`

2. **Determine resource name.** Parse the argument to determine the serializer names:
   - `Article` becomes `ArticleListSerializer`, `ArticleDetailSerializer`,
     `ArticleCreateSerializer`, `ArticleUpdateSerializer`

3. **Generate the serializer file.** Create the serializer module with:
   - `ArticleListSerializer` with summary fields for list views
   - `ArticleDetailSerializer` with all fields and nested relations
   - `ArticleCreateSerializer` with writable fields and `create()` method
   - `ArticleUpdateSerializer` with partial update support and `update()` method
   - Proper `class Meta` with `model`, `fields`, `read_only_fields`
   - Custom validation methods (`validate_<field>`, `validate`)

4. **Run quality checks.**

   ```bash
   uv run ruff format <generated_files>
   uv run ruff check <generated_files>
   ```

5. **Report results.** Show the generated file.

## Generated Files

```
<app>/serializers.py  (created or updated)
```
