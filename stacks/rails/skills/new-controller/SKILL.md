---
name: new-controller
description: Generate a RESTful Rails controller with strong params and presenter integration
---

# /new-controller

## What This Does

Generates a new RESTful controller following the project's controller pattern:
before_actions for authentication and resource loading, strong params, presenter
integration for JSON responses, and proper error handling.

## Usage

```
/new-controller Profiles            # Creates Api::V1::ProfilesController
/new-controller Admin::Companies    # Creates Api::V1::Admin::CompaniesController
/new-controller Experiences         # Creates Api::V1::ExperiencesController
```

## How It Works

1. **Read reference patterns.** Load the controller pattern from:
   - `skills/new-controller/references/controller-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-ruby.md`

2. **Determine namespace and class name.** Parse the argument:
   - `Profiles` becomes `Api::V1::ProfilesController`
   - `Admin::Companies` becomes `Api::V1::Admin::CompaniesController`

3. **Generate the controller file.** Create the controller with:
   - `frozen_string_literal: true`
   - RESTful CRUD actions (index, show, create, update, destroy)
   - `before_action :authenticate_user!`
   - `before_action :set_<resource>` for member actions
   - Strong params method
   - Presenter integration for responses
   - YARD documentation

4. **Generate the request spec.** Create the spec with:
   - Auth and unauth contexts
   - Happy path and error cases for each action
   - FactoryBot usage

5. **Add route.** Suggest the route entry for `config/routes.rb`.

6. **Run quality checks.**

   ```bash
   bundle exec rubocop -A app/controllers/<path>.rb spec/requests/<path>_spec.rb
   bundle exec rspec spec/requests/<path>_spec.rb
   ```

## Generated Files

```
app/controllers/api/v1/<resource>_controller.rb
spec/requests/api/v1/<resource>_spec.rb
```
