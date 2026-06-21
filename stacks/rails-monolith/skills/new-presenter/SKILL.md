---
name: new-presenter
description: Generate a presenter object with BasePresenter inheritance and spec
---

# /new-presenter

## What This Does

Generates a new presenter object following the project's presenter pattern:
inheriting from `BasePresenter`, exposing a `call` method that returns a hash
suitable for JSON serialization. Also generates the corresponding spec file.

## Usage

```
/new-presenter Profile                # Creates ProfilePresenter
/new-presenter Company                # Creates CompanyPresenter
/new-presenter Experience             # Creates ExperiencePresenter
```

## How It Works

1. **Read reference patterns.** Load the presenter pattern from:
   - `skills/new-presenter/references/presenter-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-ruby.md`

2. **Determine the class name.** Parse the argument:
   - `Profile` becomes `ProfilePresenter` in `app/presenters/profile_presenter.rb`

3. **Generate the presenter file.** Create the presenter with:
   - `frozen_string_literal: true`
   - `BasePresenter` inheritance
   - `call` method returning a hash with hash shorthand
   - Collection handling (single record vs array)
   - Nested data methods for associations
   - Conditional fields
   - YARD documentation

4. **Generate the spec file.** Create the spec with:
   - Single record presentation test
   - Collection presentation test
   - Conditional field tests
   - Association data tests

5. **Run quality checks.**

   ```bash
   bundle exec rubocop -A app/presenters/<name>.rb spec/presenters/<name>_spec.rb
   bundle exec rspec spec/presenters/<name>_spec.rb
   ```

## Generated Files

```
app/presenters/<model_name>_presenter.rb
spec/presenters/<model_name>_presenter_spec.rb
```
