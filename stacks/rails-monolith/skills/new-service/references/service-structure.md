# Service Object Structure Template

The canonical structure for all service objects in this Rails application.

---

## File Layout

```
app/services/
  application_service.rb          # Base class
  <namespace>/
    <service_name>_service.rb     # Service implementation
```

```
spec/services/
  <namespace>/
    <service_name>_service_spec.rb  # Service spec
```

---

## Service Template

```ruby
# frozen_string_literal: true

module <Namespace>
  # <One-line description of what this service does.>
  #
  # <Optional longer description explaining the business context,
  # when this service should be used, and any important caveats.>
  #
  # @example
  #   <Namespace>::<ServiceName>.new(<param>:).call
  class <ServiceName> < ApplicationService
    # @param <param> [<Type>] <description>
    # @param <optional_param> [<Type>] <description>
    def initialize(<param>:, <optional_param>: nil)
      @<param> = <param>
      @<optional_param> = <optional_param>
    end

    # <Description of what call does.>
    #
    # @return [<Type>] <description of return value>
    # @raise [<ErrorClass>] <when this error occurs>
    def call
      return <early_return> if <guard_condition>

      <main_logic>
    end

    private

    attr_reader :<param>, :<optional_param>

    # <Description of private helper.>
    #
    # @return [<Type>] <description>
    def <helper_method>
      # implementation
    end
  end
end
```

---

## ApplicationService Base

```ruby
# frozen_string_literal: true

# Base class for all service objects. Provides a class-level .call
# convenience method that instantiates and calls the service in one step.
#
# @example
#   # These are equivalent:
#   Users::SyncService.new(user:).call
#   Users::SyncService.call(user:)
class ApplicationService
  # Instantiates the service and calls it.
  #
  # @return [Object] the result of #call
  def self.call(...)
    new(...).call
  end
end
```

---

## Naming Conventions

| Concept         | Naming Pattern                  | Example                              |
|-----------------|--------------------------------|--------------------------------------|
| Namespace       | Business domain module         | `BulkImport`, `Sync`, `Users`        |
| Class name      | Action + optional noun + `Service` | `ProfilesService`, `SyncService` |
| File path       | Snake_case of full class path  | `bulk_import/profiles_service.rb`    |
| Spec path       | Mirrors service path           | `spec/services/bulk_import/profiles_service_spec.rb` |

---

## Rules

1. **One public method**: `call` is the only public instance method
2. **Keyword arguments**: `initialize` always uses keyword args
3. **Guard clauses**: Return early at the top of `call` for invalid states
4. **Private attr_reader**: Expose instance variables via private attr_reader
5. **No side effects in initialize**: Only assign variables, do not perform logic
6. **Return value**: `call` returns a meaningful value (result object, boolean, or data)
7. **Error handling**: Rescue specific exceptions; log and re-raise or return error result
8. **Testability**: Services should be easy to test with clear inputs and outputs
