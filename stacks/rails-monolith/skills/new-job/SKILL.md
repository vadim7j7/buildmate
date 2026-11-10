---
name: new-job
description: Generate a namespaced ActiveJob background job with retry config and spec
---

# /new-job

## What This Does

Generates a new ActiveJob background job (runs on the project's adapter: Sidekiq,
Solid Queue or GoodJob) following the project's job pattern: namespaced
under a module, configured with queue and retry settings, delegating to a service
object. Also generates the corresponding spec file.

## Usage

```
/new-job AirtableSync                 # Creates Sync::AirtableSyncJob
/new-job BulkImport::Profiles         # Creates BulkImport::ProfilesJob
/new-job Notifications::Welcome       # Creates Notifications::WelcomeJob
```

## How It Works

1. **Read reference patterns.** Load the job pattern from:
   - `skills/new-job/references/job-examples.md`
   - `patterns/rails-monolith-patterns.md`
   - `styles/backend-ruby.md`

2. **Determine namespace and class name.** Parse the argument to determine the
   module namespace and class name:
   - `AirtableSync` becomes `Sync::AirtableSyncJob`
   - `BulkImport::Profiles` becomes `BulkImport::ProfilesJob`

3. **Generate the job file.** Create the job file with:
   - `frozen_string_literal: true`
   - Module namespace
   - YARD documentation
   - `ApplicationJob` inheritance
   - Queue configuration (`queue_as`)
   - `retry_on` / `discard_on` declarations (retry count lives in `retry_on attempts:`)
   - `sidekiq_options` only when the project's adapter is Sidekiq (check
     `config.active_job.queue_adapter`); it raises `NoMethodError` on other adapters
   - `perform` method that delegates to a service
   - Error handling

4. **Generate the spec file.** Create the spec with:
   - Queue configuration tests
   - Service delegation tests
   - Error handling tests
   - Edge case tests (record not found, already processed)

5. **Run quality checks.**

   ```bash
   bundle exec rubocop -A app/jobs/<path>.rb spec/jobs/<path>_spec.rb
   bundle exec rspec spec/jobs/<path>_spec.rb
   ```

## Generated Files

```
app/jobs/<namespace>/<job_name>.rb
spec/jobs/<namespace>/<job_name>_spec.rb
```
