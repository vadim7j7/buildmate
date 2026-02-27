---
name: new-model
description: Generate a Django model with fields, validators, and test
---

# /new-model

## What This Does

Generates a Django model with proper field definitions, validators, Meta options,
and a corresponding test file. Also generates the migration.

## Usage

```
/new-model Article                  # Creates Article model
/new-model UserProfile              # Creates UserProfile model
/new-model OrderItem                # Creates OrderItem model
```

## How It Works

1. **Read reference patterns.** Load the model pattern from:
   - `patterns/django-patterns.md`
   - `styles/backend-python.md`

2. **Determine the model name and attributes.** Parse the argument and ask for
   or infer attributes based on the model name and context.

3. **Generate the model file.** Create or update the app's `models.py` with:
   - `from django.db import models`
   - Class inheriting from `models.Model`
   - Field definitions with appropriate types (`CharField`, `ForeignKey`, etc.)
   - `__str__` method
   - `class Meta` with `ordering`, `verbose_name`, `verbose_name_plural`
   - Validators and constraints
   - Custom managers or querysets if needed
   - Docstring on the class

4. **Register in admin.** Add a basic admin registration in `admin.py`:

   ```python
   @admin.register(ModelName)
   class ModelNameAdmin(admin.ModelAdmin):
       list_display = [...]
       search_fields = [...]
   ```

5. **Generate the migration.**

   ```bash
   uv run python manage.py makemigrations
   ```

6. **Generate the test file.** Create tests with:
   - Model creation tests
   - Validation tests (required fields, constraints)
   - `__str__` method test
   - Relationship tests (if applicable)
   - Custom manager/queryset tests

7. **Run quality checks.**

   ```bash
   uv run python manage.py migrate
   uv run ruff format <generated_files>
   uv run ruff check <generated_files>
   uv run pytest <test_file> -v
   ```

## Generated Files

```
<app>/models.py          (updated)
<app>/admin.py           (updated)
<app>/migrations/NNNN_<description>.py
<app>/tests/test_models.py  (created or updated)
```
