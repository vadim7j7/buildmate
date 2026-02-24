---
name: new-form
description: Generate a new form component with validation and async submission
---

# /new-form

## What This Does

Creates a new form component with TypeScript types, validation rules, IIFE
async submission, and user feedback notifications. Uses the project's
configured UI library for form components and notifications.

## Usage

```
/new-form CreateProject
/new-form EditProfile
/new-form LoginForm
/new-form InviteTeamMember
```

## How It Works

### 1. Determine Form Fields

Based on the form name, infer:
- What fields are needed
- What validation rules apply
- What the submit action does

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` for conventions
- `skills/new-form/references/form-examples.md` for examples
- The project's UI library style guide (in `styles/`) for form components
- Existing forms in `src/components/` for project patterns

### 3. Generate Files

#### Form Component: `src/components/<Name>Form.tsx`

```typescript
'use client';

type <Name>FormValues = {
  // form field types
};

type <Name>FormProps = {
  onSubmit: (values: <Name>FormValues) => Promise<void>;
  onCancel?: () => void;
  initialValues?: Partial<<Name>FormValues>;
  submitLabel?: string;
};

export function <Name>Form({ onSubmit, onCancel, initialValues, submitLabel = 'Submit' }: <Name>FormProps) {
  // Use the project's form handling approach (e.g., @mantine/form, react-hook-form, native forms)
  // See the UI library style guide for form patterns

  const handleSubmit = (values: <Name>FormValues) => {
    (async () => {
      try {
        await onSubmit(values);
      } catch {
        // Show error notification using UI library
      }
    })();
  };

  return (
    <form onSubmit={/* form handler */}>
      {/* Form inputs using UI library components */}
      {/* Submit and cancel buttons */}
    </form>
  );
}
```

#### Test File: `src/components/<Name>Form.test.tsx`

Tests for validation, successful submission, and error handling.

### 4. Verify

Run `npx tsc --noEmit` to verify the form compiles.

## Rules

- All forms use `'use client'` directive
- Use the project's form handling library (see style guides)
- Validation rules defined in the form configuration
- Async submission via IIFE pattern
- User feedback via the UI library's notification system
- Support `initialValues` prop for edit forms
- Support `onCancel` prop for navigation
- Use `type` for form values and props

## Output

```
Created:
  src/components/<Name>Form.tsx       -- Form component
  src/components/<Name>Form.test.tsx  -- Unit tests

Verified:
  npx tsc --noEmit  -- PASS
```
