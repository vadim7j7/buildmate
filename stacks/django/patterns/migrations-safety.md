# Safe Django Migrations (Zero-Downtime)

Read when a migration changes an existing table, moves data, or must run while
the old code is still serving traffic. During a rolling deploy the **old code
runs against the new schema**: every migration must be compatible with both.

## Review Every Generated Migration

```bash
uv run python manage.py makemigrations <app>
uv run python manage.py sqlmigrate <app> <number>     # read the SQL it will run
uv run python manage.py makemigrations --check --dry-run   # CI: nothing missing
```

## Expand, Migrate, Contract

| Change | Safe sequence |
|--------|---------------|
| Add a column | Nullable, or with `db_default=` (Django 5.0+, set in the database) |
| Add NOT NULL to existing column | 1) add nullable 2) backfill 3) deploy code that always writes it 4) `null=False` |
| Rename a column | 1) add new 2) write both, backfill 3) read new 4) drop old; or `db_column=` to keep the DB name |
| Drop a column | 1) remove all code use (and from `Meta`/serializers) and deploy 2) then the migration |
| Rename a model/table | `SeparateDatabaseAndState` or `db_table=` to keep the table name |
| Add an index (PostgreSQL, big table) | `AddIndexConcurrently` in a non-atomic migration |

A `default=` (without `db_default`) is applied by Django only for rows that
exist when the migration runs; rows inserted by old code afterwards get NULL.

## Indexes Without Locking (PostgreSQL)

```python
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False  # CONCURRENTLY cannot run in a transaction

    dependencies = [("projects", "0012_project_status")]

    operations = [
        AddIndexConcurrently(
            "project",
            models.Index(fields=["owner", "status"], name="project_owner_status_idx"),
        ),
    ]
```

Add the same index to `Meta.indexes` so the state matches. Use
`RemoveIndexConcurrently` to drop.

## Data Migrations: `RunPython` With a Reverse

```python
from django.db import migrations


def backfill_slug(apps, schema_editor):
    # Historical model: apps.get_model, never `from projects.models import Project`
    Project = apps.get_model("projects", "Project")
    batch = []
    for project in Project.objects.filter(slug="").only("id", "name").iterator(chunk_size=1000):
        project.slug = slugify_name(project.name)
        batch.append(project)
        if len(batch) >= 1000:
            Project.objects.bulk_update(batch, ["slug"])
            batch.clear()
    Project.objects.bulk_update(batch, ["slug"])


def slugify_name(name: str) -> str:
    from django.utils.text import slugify

    return slugify(name)[:50]


class Migration(migrations.Migration):
    dependencies = [("projects", "0013_project_slug")]

    operations = [
        # The backfill is safe to leave on rollback: reverse is a no-op
        migrations.RunPython(backfill_slug, reverse_code=migrations.RunPython.noop),
    ]
```

Rules:
- Always pass `reverse_code` (`RunPython.noop` when undoing is unnecessary); a
  migration without it cannot be rolled back.
- Use historical models from `apps.get_model`: no custom methods or managers,
  no model `save()` signals. Copy any helper logic into the migration.
- Idempotent: filter only rows still needing the change.
- Batch with `iterator()` + `bulk_update`; a single `UPDATE ... ` via
  `.update()` is better when the new value is an expression (`F()`, `Lower()`).
- Big tables (millions of rows): put the backfill in a management command run
  after deploy, not in the migration (it holds a transaction and blocks deploys).
- Keep schema and data operations in separate migrations.

## `SeparateDatabaseAndState`

Change Django's model state without touching the database (or the reverse).
Typical case: rename a model but keep its table.

```python
class Migration(migrations.Migration):
    dependencies = [("billing", "0007_invoice")]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[migrations.RenameModel("Invoice", "Bill")],
            database_operations=[],  # table stays billing_invoice
        ),
    ]
```

with `class Meta: db_table = "billing_invoice"` on `Bill`. Same tool for moving a
model between apps (state: delete in one app, create in the other; database:
nothing, keep `db_table`).

## Locks and Timeouts (PostgreSQL)

Even "instant" DDL waits for an `ACCESS EXCLUSIVE` lock and queues every query
behind it. Make migrations fail fast instead of stalling the site:

```python
migrations.RunSQL("SET lock_timeout = '5s';", reverse_sql=migrations.RunSQL.noop)
```

as the first operation, and retry the deploy when it times out.

## Housekeeping

- One migration per logical change; name it (`makemigrations -n add_project_slug`).
- Two branches adding migrations to the same app produce two leaves:
  `makemigrations --merge`, or renumber the later one before merging.
- `squashmigrations` only after every environment has applied the originals.
- Never edit a migration that has run in a shared environment; add a new one.
