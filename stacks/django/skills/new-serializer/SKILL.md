---
name: new-serializer
description: Generate a Django REST Framework serializer set
---

# /new-serializer

## What This Does

Generates DRF serializers for a model with read, create, and update variants.

## Usage

```
/new-serializer projects     # Creates serializers for Project model
/new-serializer users        # Creates serializers for User model
```

## How It Works

1. **Read reference patterns** from `patterns/django-patterns.md` and `styles/backend-python.md`
2. **Read the model** to determine fields and relationships
3. **Generate serializers**: base read serializer and create serializer
4. **Generate test file** for serializer validation
5. **Run quality checks**: `uv run ruff format && uv run ruff check && uv run mypy`

## Generated Files

```
src/<app>/serializers.py (or serializers/<resource>.py)
tests/<app>/test_serializers.py
```
