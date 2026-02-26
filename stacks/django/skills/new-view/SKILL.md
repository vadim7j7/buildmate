---
name: new-view
description: Generate a Django REST Framework ViewSet with serializers and URL config
---

# /new-view

## What This Does

Generates a Django REST Framework ViewSet with serializers, URL configuration,
admin registration, and test file.

## Usage

```
/new-view projects     # Creates views, serializers, URLs for projects
/new-view users        # Creates views, serializers, URLs for users
```

## How It Works

1. **Read reference patterns** from `patterns/django-patterns.md` and `styles/backend-python.md`
2. **Generate or update model** if it doesn't exist
3. **Generate serializers** (read and create)
4. **Generate ViewSet** with CRUD operations
5. **Generate URL config** with DRF router
6. **Register in admin** if not already registered
7. **Generate test file** with pytest and APIClient
8. **Run quality checks**: `uv run ruff format && uv run ruff check && uv run mypy && uv run pytest`

## Generated Files

```
src/<app>/views.py (or views/<resource>.py)
src/<app>/serializers.py
src/<app>/urls.py
src/<app>/admin.py (updated)
tests/<app>/test_views.py
```
