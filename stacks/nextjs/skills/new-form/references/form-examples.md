# Mantine Form Examples

## Example 1: Simple Create Form

A form for creating a new resource with validation and notifications.

```typescript
// src/components/CreateProjectForm.tsx
'use client';

import { useForm } from '@mantine/form';
import { TextInput, Textarea, Button, Stack, Group } from '@mantine/core';
import { showNotification } from '@mantine/notifications';

type CreateProjectFormValues = {
  name: string;
  description: string;
};

type CreateProjectFormProps = {
  onSubmit: (values: CreateProjectFormValues) => Promise<void>;
  onCancel?: () => void;
};

/** Form for creating a new project with name and description */
export function CreateProjectForm({ onSubmit, onCancel }: CreateProjectFormProps) {
  const form = useForm<CreateProjectFormValues>({
    initialValues: {
      name: '',
      description: '',
    },
    validate: {
      name: (value) => {
        if (value.trim().length < 2) return 'Name must be at least 2 characters';
        if (value.trim().length > 100) return 'Name must be less than 100 characters';
        return null;
      },
      description: (value) =>
        value.trim().length === 0 ? 'Description is required' : null,
    },
  });

  const handleSubmit = form.onSubmit((values) => {
    (async () => {
      try {
        await onSubmit(values);
        showNotification({
          title: 'Success',
          message: 'Project created successfully',
          color: 'green',
        });
        form.reset();
      } catch {
        showNotification({
          title: 'Error',
          message: 'Failed to create project. Please try again.',
          color: 'red',
        });
      }
    })();
  });

  return (
    <form onSubmit={handleSubmit}>
      <Stack>
        <TextInput
          label="Project Name"
          placeholder="Enter project name"
          required
          {...form.getInputProps('name')}
        />
        <Textarea
          label="Description"
          placeholder="Describe your project"
          required
          minRows={3}
          {...form.getInputProps('description')}
        />
        <Group justify="flex-end">
          {onCancel && (
            <Button variant="default" onClick={onCancel}>
              Cancel
            </Button>
          )}
          <Button type="submit">Create Project</Button>
        </Group>
      </Stack>
    </form>
  );
}
```

---

## Example 2: Edit Form with Initial Values

A form pre-populated with existing data for editing.

```typescript
// src/components/ProjectForm.tsx
'use client';

import { useForm } from '@mantine/form';
import { TextInput, Textarea, Select, Button, Stack, Group } from '@mantine/core';
import { showNotification } from '@mantine/notifications';

type ProjectFormValues = {
  name: string;
  description: string;
  status: 'active' | 'archived' | 'draft';
};

type ProjectFormProps = {
  onSubmit: (values: ProjectFormValues) => Promise<void>;
  onCancel?: () => void;
  initialValues?: Partial<ProjectFormValues>;
  submitLabel?: string;
};

/** Reusable form for creating or editing a project */
export function ProjectForm({
  onSubmit,
  onCancel,
  initialValues,
  submitLabel = 'Save',
}: ProjectFormProps) {
  const form = useForm<ProjectFormValues>({
    initialValues: {
      name: '',
      description: '',
      status: 'draft',
      ...initialValues,
    },
    validate: {
      name: (value) => {
        if (value.trim().length < 2) return 'Name must be at least 2 characters';
        if (value.trim().length > 100) return 'Name must be under 100 characters';
        return null;
      },
      description: (value) =>
        value.trim().length === 0 ? 'Description is required' : null,
    },
  });

  const handleSubmit = form.onSubmit((values) => {
    (async () => {
      try {
        await onSubmit(values);
      } catch {
        showNotification({
          title: 'Error',
          message: 'Failed to save. Please try again.',
          color: 'red',
        });
      }
    })();
  });

  return (
    <form onSubmit={handleSubmit}>
      <Stack>
        <TextInput
          label="Project Name"
          placeholder="Enter project name"
          required
          {...form.getInputProps('name')}
        />
        <Textarea
          label="Description"
          placeholder="Describe your project"
          required
          minRows={3}
          {...form.getInputProps('description')}
        />
        <Select
          label="Status"
          data={[
            { value: 'active', label: 'Active' },
            { value: 'archived', label: 'Archived' },
            { value: 'draft', label: 'Draft' },
          ]}
          {...form.getInputProps('status')}
        />
        <Group justify="flex-end">
          {onCancel && (
            <Button variant="default" onClick={onCancel}>
              Cancel
            </Button>
          )}
          <Button type="submit">{submitLabel}</Button>
        </Group>
      </Stack>
    </form>
  );
}
```

---

## Example 3: Login Form with Email/Password

```typescript
// src/components/LoginForm.tsx
'use client';

import { useForm } from '@mantine/form';
import { TextInput, PasswordInput, Button, Stack, Anchor, Text, Group } from '@mantine/core';
import { showNotification } from '@mantine/notifications';

type LoginFormValues = {
  email: string;
  password: string;
};

type LoginFormProps = {
  onSubmit: (values: LoginFormValues) => Promise<void>;
  onForgotPassword?: () => void;
};

/** Login form with email and password fields */
export function LoginForm({ onSubmit, onForgotPassword }: LoginFormProps) {
  const form = useForm<LoginFormValues>({
    initialValues: {
      email: '',
      password: '',
    },
    validate: {
      email: (value) =>
        /^\S+@\S+\.\S+$/.test(value) ? null : 'Please enter a valid email address',
      password: (value) =>
        value.length >= 8 ? null : 'Password must be at least 8 characters',
    },
  });

  const handleSubmit = form.onSubmit((values) => {
    (async () => {
      try {
        await onSubmit(values);
      } catch {
        showNotification({
          title: 'Login Failed',
          message: 'Invalid email or password. Please try again.',
          color: 'red',
        });
      }
    })();
  });

  return (
    <form onSubmit={handleSubmit}>
      <Stack>
        <TextInput
          label="Email"
          placeholder="your@email.com"
          required
          {...form.getInputProps('email')}
        />
        <PasswordInput
          label="Password"
          placeholder="Enter your password"
          required
          {...form.getInputProps('password')}
        />
        {onForgotPassword && (
          <Group justify="flex-end">
            <Anchor component="button" type="button" size="sm" onClick={onForgotPassword}>
              Forgot password?
            </Anchor>
          </Group>
        )}
        <Button type="submit" fullWidth>
          Sign In
        </Button>
      </Stack>
    </form>
  );
}
```

---

## Example 4: Multi-Step Form

```typescript
// src/components/OnboardingForm.tsx
'use client';

import { useState } from 'react';
import { useForm } from '@mantine/form';
import { TextInput, Select, Textarea, Button, Stack, Group, Stepper } from '@mantine/core';
import { showNotification } from '@mantine/notifications';

type OnboardingFormValues = {
  // Step 1
  name: string;
  email: string;
  // Step 2
  company: string;
  role: string;
  // Step 3
  bio: string;
};

type OnboardingFormProps = {
  onSubmit: (values: OnboardingFormValues) => Promise<void>;
};

/** Multi-step onboarding form */
export function OnboardingForm({ onSubmit }: OnboardingFormProps) {
  const [activeStep, setActiveStep] = useState(0);

  const form = useForm<OnboardingFormValues>({
    initialValues: {
      name: '',
      email: '',
      company: '',
      role: '',
      bio: '',
    },
    validate: {
      name: (value) => (value.trim().length < 2 ? 'Name is required' : null),
      email: (value) => (/^\S+@\S+\.\S+$/.test(value) ? null : 'Invalid email'),
      company: (value) => (value.trim().length < 1 ? 'Company is required' : null),
      role: (value) => (value ? null : 'Please select a role'),
    },
  });

  const validateStep = (step: number): boolean => {
    if (step === 0) {
      const nameError = form.validateField('name');
      const emailError = form.validateField('email');
      return !nameError.hasError && !emailError.hasError;
    }
    if (step === 1) {
      const companyError = form.validateField('company');
      const roleError = form.validateField('role');
      return !companyError.hasError && !roleError.hasError;
    }
    return true;
  };

  const nextStep = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prev) => Math.min(prev + 1, 2));
    }
  };

  const prevStep = () => setActiveStep((prev) => Math.max(prev - 1, 0));

  const handleSubmit = form.onSubmit((values) => {
    (async () => {
      try {
        await onSubmit(values);
        showNotification({
          title: 'Welcome!',
          message: 'Your profile has been set up',
          color: 'green',
        });
      } catch {
        showNotification({
          title: 'Error',
          message: 'Setup failed. Please try again.',
          color: 'red',
        });
      }
    })();
  });

  return (
    <form onSubmit={handleSubmit}>
      <Stepper active={activeStep}>
        <Stepper.Step label="Personal">
          <Stack mt="md">
            <TextInput label="Name" required {...form.getInputProps('name')} />
            <TextInput label="Email" required {...form.getInputProps('email')} />
          </Stack>
        </Stepper.Step>

        <Stepper.Step label="Work">
          <Stack mt="md">
            <TextInput label="Company" required {...form.getInputProps('company')} />
            <Select
              label="Role"
              required
              data={['Developer', 'Designer', 'Manager', 'Other']}
              {...form.getInputProps('role')}
            />
          </Stack>
        </Stepper.Step>

        <Stepper.Step label="Profile">
          <Stack mt="md">
            <Textarea label="Bio" placeholder="Tell us about yourself" minRows={4} {...form.getInputProps('bio')} />
          </Stack>
        </Stepper.Step>
      </Stepper>

      <Group justify="flex-end" mt="xl">
        {activeStep > 0 && (
          <Button variant="default" onClick={prevStep}>
            Back
          </Button>
        )}
        {activeStep < 2 ? (
          <Button onClick={nextStep}>Next</Button>
        ) : (
          <Button type="submit">Complete Setup</Button>
        )}
      </Group>
    </form>
  );
}
```

---

## Form Validation Rules Reference

```typescript
const form = useForm({
  validate: {
    // Required string
    name: (value) => (value.trim().length === 0 ? 'Required' : null),

    // Minimum length
    name: (value) => (value.trim().length < 2 ? 'At least 2 characters' : null),

    // Maximum length
    name: (value) => (value.length > 100 ? 'Must be under 100 characters' : null),

    // Email format
    email: (value) => (/^\S+@\S+\.\S+$/.test(value) ? null : 'Invalid email'),

    // Password strength
    password: (value) => {
      if (value.length < 8) return 'At least 8 characters';
      if (!/[A-Z]/.test(value)) return 'Must contain uppercase letter';
      if (!/[0-9]/.test(value)) return 'Must contain number';
      return null;
    },

    // Confirm password match
    confirmPassword: (value, values) =>
      value !== values.password ? 'Passwords do not match' : null,

    // URL format
    website: (value) => {
      if (!value) return null; // Optional
      try {
        new URL(value);
        return null;
      } catch {
        return 'Invalid URL';
      }
    },

    // Number range
    age: (value) => {
      if (value < 0 || value > 150) return 'Invalid age';
      return null;
    },

    // Select required
    role: (value) => (value ? null : 'Please select a role'),

    // Array minimum items
    tags: (value) => (value.length < 1 ? 'At least one tag required' : null),
  },
});
```
