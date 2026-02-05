---
name: new-form
description: Generate a new Mantine form component with useForm, validation, and async submission
---

# /new-form

## What This Does

Creates a new form component using `@mantine/form` with TypeScript types,
validation rules, IIFE async submission, and `showNotification` for user
feedback.

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
- Existing forms in `src/components/` for project patterns

### 3. Generate Files

#### Form Component: `src/components/<Name>Form.tsx`

```typescript
'use client';

import { useForm } from '@mantine/form';
import { TextInput, Button, Stack } from '@mantine/core';
import { showNotification } from '@mantine/notifications';

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
  const form = useForm<<Name>FormValues>({
    initialValues: {
      // defaults merged with initialValues
      ...initialValues,
    },
    validate: {
      // validation rules
    },
  });

  const handleSubmit = form.onSubmit((values) => {
    (async () => {
      try {
        await onSubmit(values);
      } catch {
        showNotification({ title: 'Error', message: 'Submission failed', color: 'red' });
      }
    })();
  });

  return (
    <form onSubmit={handleSubmit}>
      <Stack>
        {/* Form inputs */}
        <Group justify="flex-end">
          {onCancel && <Button variant="default" onClick={onCancel}>Cancel</Button>}
          <Button type="submit">{submitLabel}</Button>
        </Group>
      </Stack>
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
- Form state via `@mantine/form` `useForm` hook
- Validation rules in `useForm({ validate: {} })`
- Async submission via IIFE pattern in `form.onSubmit`
- User feedback via `showNotification`
- Support `initialValues` prop for edit forms
- Support `onCancel` prop for navigation
- Use `type` for form values and props
- Mantine form inputs with `{...form.getInputProps('fieldName')}`

## Output

```
Created:
  src/components/<Name>Form.tsx       -- Form component
  src/components/<Name>Form.test.tsx  -- Unit tests

Verified:
  npx tsc --noEmit  -- PASS
```
