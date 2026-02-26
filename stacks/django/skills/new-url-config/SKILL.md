---
name: new-url-config
description: Generate Django URL configuration with DRF router
---

# /new-url-config

## What This Does

Generates Django URL configuration using DRF routers for ViewSet registration.

## Usage

```
/new-url-config projects     # Creates URL config for project ViewSet
/new-url-config users        # Creates URL config for user ViewSet
```

## How It Works

1. **Read reference patterns** from `patterns/django-patterns.md`
2. **Generate URL config** with `DefaultRouter` and ViewSet registration
3. **Include in root URL config** if not already registered
4. **Run quality checks**: `uv run ruff format && uv run ruff check`

## Generated Files

```
src/<app>/urls.py
src/config/urls.py (updated to include app URLs)
```
