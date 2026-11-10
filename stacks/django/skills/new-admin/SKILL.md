---
name: new-admin
description: Register a model in the Django admin with list display, search, filters and query-efficient lists
---

# /new-admin

## What This Does

Generates or updates `<app>/admin.py` with a `ModelAdmin` that is usable on
real data volumes: useful columns, search, filters, no N+1 on the change list,
and no accidental edits of system fields.

## Usage

```
/new-admin projects Project
/new-admin billing Invoice --inline InvoiceLine
```

## How It Works

1. **Read** the model (fields, FKs, `__str__`), `.claude/patterns/django-patterns.md`
   (Admin Pattern) and the app's existing `admin.py`.

2. **Write the ModelAdmin.**

   ```python
   from django.contrib import admin

   from .models import Invoice, InvoiceLine


   class InvoiceLineInline(admin.TabularInline):
       model = InvoiceLine
       extra = 0
       autocomplete_fields = ["product"]


   @admin.register(Invoice)
   class InvoiceAdmin(admin.ModelAdmin):
       list_display = ["number", "customer", "status", "total", "issued_at"]
       list_filter = ["status", ("issued_at", admin.DateFieldListFilter)]
       search_fields = ["number", "customer__name", "customer__email"]
       list_select_related = ["customer"]          # every FK shown in list_display
       autocomplete_fields = ["customer"]          # FK widgets: no giant <select>
       readonly_fields = ["number", "created_at", "updated_at"]
       date_hierarchy = "issued_at"
       ordering = ["-issued_at"]
       list_per_page = 50
       show_full_result_count = False              # skip COUNT(*) on big tables
       inlines = [InvoiceLineInline]

       @admin.display(description="Total", ordering="total_cents")
       def total(self, obj: Invoice) -> str:
           return f"{obj.total_cents / 100:.2f}"
   ```

   Rules:
   - `list_select_related` for every FK in `list_display`; for counts or
     reverse relations, override `get_queryset` with `annotate()` /
     `prefetch_related()`, never a query per row in a display method.
   - FKs to large tables use `autocomplete_fields` (the target admin needs
     `search_fields`) or `raw_id_fields`.
   - `search_fields` only on indexed or small columns; prefix with `^` / `=` for
     starts-with / exact lookups on big tables.
   - System-managed fields (timestamps, external ids, computed totals) are
     `readonly_fields`.
   - Bulk changes go in `actions` that call a service, with a confirmation
     message (`self.message_user`).
   - Sensitive models: override `has_delete_permission` / `has_add_permission`
     rather than relying on staff discipline.

3. **Test** the change list and change form load for a superuser with data
   present, and that the list query count does not grow with rows:

   ```python
   def test_invoice_changelist(admin_client, invoice_factory, django_assert_max_num_queries):
       invoice_factory.create_batch(5)
       with django_assert_max_num_queries(10):
           response = admin_client.get("/admin/billing/invoice/")
       assert response.status_code == 200
   ```

4. **Run quality checks.**

   ```bash
   uv run ruff format <app>/admin.py && uv run ruff check <app>/admin.py
   uv run python manage.py check
   uv run pytest <app>/tests/ -k admin -v
   ```

## Generated Files

```
<app>/admin.py
<app>/tests/test_admin.py
```
