---
name: new-command
description: Generate a Django management command (backfill, report, maintenance) with dry-run and a test
---

# /new-command

## What This Does

Generates `<app>/management/commands/<name>.py`: a `BaseCommand` for one-off
data fixes, backfills, reports or scheduled maintenance, with `--dry-run`,
batching and a test.

## Usage

```
/new-command projects backfill_slugs
/new-command billing send_overdue_reminders
```

## How It Works

1. **Read** `.claude/patterns/django-patterns.md`, `.claude/patterns/backend-patterns.md`
   (services) and an existing command if the project has one.

2. **Create the package files** if missing: `<app>/management/__init__.py`,
   `<app>/management/commands/__init__.py`.

3. **Write the command.** The command parses arguments and reports; the work is
   in a service so it can be tested and reused:

   ```python
   from django.core.management.base import BaseCommand, CommandError

   from projects.services.slugs import SlugBackfillService


   class Command(BaseCommand):
       help = "Fill empty project slugs from the project name."

       def add_arguments(self, parser):
           parser.add_argument("--dry-run", action="store_true", help="Count only, write nothing")
           parser.add_argument("--batch-size", type=int, default=1000)
           parser.add_argument("--project-id", type=int, help="Limit to one project")

       def handle(self, *args, dry_run: bool, batch_size: int, project_id: int | None, **options):
           if batch_size <= 0:
               raise CommandError("--batch-size must be positive")
           result = SlugBackfillService().run(
               dry_run=dry_run, batch_size=batch_size, project_id=project_id
           )
           prefix = "[dry run] " if dry_run else ""
           self.stdout.write(self.style.SUCCESS(f"{prefix}{result.updated} of {result.matched} updated"))
   ```

   Rules:
   - Idempotent: select only rows still needing the change; a re-run is a no-op.
   - Batched (`iterator(chunk_size=...)` + `bulk_update`, or `.update()` with an
     expression); never load a whole table.
   - `--dry-run` that writes nothing and prints the same counts.
   - Write output with `self.stdout` / `self.stderr` (tests capture them), never `print`.
   - Fail with `CommandError` (non-zero exit), not a bare exception.
   - Long writes: a transaction per batch, not one for the whole run.

4. **Write the test** in `<app>/tests/test_commands.py`:

   ```python
   from io import StringIO

   import pytest
   from django.core.management import call_command

   pytestmark = pytest.mark.django_db


   def test_backfill_slugs_dry_run_writes_nothing(project_factory):
       project = project_factory(slug="")
       out = StringIO()
       call_command("backfill_slugs", "--dry-run", stdout=out)
       project.refresh_from_db()
       assert project.slug == ""
       assert "1 of 1" in out.getvalue()
   ```

   Also: the real run updates, a second run updates 0.

5. **Run quality checks.**

   ```bash
   uv run ruff format <app>/ && uv run ruff check <app>/
   uv run pytest <app>/tests/test_commands.py -v
   ```

## Generated Files

```
<app>/management/__init__.py
<app>/management/commands/__init__.py
<app>/management/commands/<name>.py
<app>/services/<name>.py           (the logic, if not existing)
<app>/tests/test_commands.py
```
