# Ruby Style Guide

Mandatory style rules for all Ruby code in this project. These are enforced by RuboCop
and by code review.

---

## 1. File Headers

Every Ruby file MUST start with the frozen string literal pragma:

```ruby
# frozen_string_literal: true
```

---

## 2. String Literals

**Always use single quotes** unless string interpolation is needed:

```ruby
# GOOD
name = 'John'
greeting = "Hello, #{name}"

# BAD
name = "John"
```

---

## 3. Hash Shorthand

Use Ruby 3.1+ hash shorthand when key and value names match:

```ruby
# GOOD
{ id:, name:, email: }

# BAD
{ id: id, name: name, email: email }
```

---

## 4. Guard Clauses

Use early returns instead of wrapping code in conditionals:

```ruby
# GOOD
def process(item)
  return if item.nil?
  return unless item.valid?

  do_work(item)
end

# BAD
def process(item)
  if item && item.valid?
    do_work(item)
  end
end
```

---

## 5. YARD Documentation

All public methods MUST have YARD documentation:

```ruby
# Processes the given item and returns the result.
#
# @param item [Item] the item to process
# @return [Result] the processing result
# @raise [Errors::ValidationError] if item is invalid
# @example
#   processor.process(item)
def process(item)
  # ...
end
```

---

## 6. Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Classes | `PascalCase` | `UserService` |
| Modules | `PascalCase` | `Authentication` |
| Methods | `snake_case` | `find_by_email` |
| Variables | `snake_case` | `user_name` |
| Constants | `SCREAMING_SNAKE` | `MAX_RETRIES` |
| Predicates | `snake_case?` | `active?` |
| Dangerous | `snake_case!` | `save!` |
| Files | `snake_case.rb` | `user_service.rb` |

---

## 7. Method Organization

Order methods within a class:

1. Class methods (`self.` methods)
2. `initialize`
3. Public instance methods
4. `private` keyword
5. `attr_reader` / `attr_accessor`
6. Private methods

---

## 8. N+1 Query Prevention

Always eager-load associations when iterating:

```ruby
# GOOD
User.eager(:posts).all.each { |u| u.posts }

# BAD - N+1 query
User.all.each { |u| u.posts }
```

---

## 9. Error Handling

Rescue specific exceptions:

```ruby
# GOOD
rescue Errors::NotFoundError => e
  logger.error("Not found: #{e.message}")

# BAD
rescue => e
  logger.error(e.message)

# BAD
rescue StandardError
  # too broad
```

---

## 10. Conditional Formatting

```ruby
# Single-line for simple conditions
return if done?
raise ArgumentError, 'invalid' unless valid?

# Multi-line for complex logic
if complex_condition? && another_check?
  perform_action
  log_result
end
```

---

## 11. Collection Methods

Prefer Ruby's collection methods over manual iteration:

```ruby
# GOOD
users.select(&:active?).map(&:email)
items.reject { |i| i.expired? }
values.sum(&:amount)

# BAD
result = []
users.each do |u|
  result << u.email if u.active?
end
```

---

## 12. RuboCop Enforcement

RuboCop checks and enforces these rules:

```bash
# Check style
bundle exec rubocop

# Auto-fix safe issues
bundle exec rubocop -A

# Check specific files
bundle exec rubocop path/to/file.rb
```

All code MUST pass `bundle exec rubocop` before it can be committed.
