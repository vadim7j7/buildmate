# Form Examples

> **Note:** These examples use plain HTML form elements. Replace with components
> from your project's configured UI library and form handling approach as specified
> in the style guides.

## Example 1: Simple Create Form

A form for creating a new resource with validation and notifications.

```typescript
// src/components/CreateProjectForm.tsx
'use client';

import { useState } from 'react';

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
  const [values, setValues] = useState<CreateProjectFormValues>({
    name: '',
    description: '',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof CreateProjectFormValues, string>>>({});
  const [submitting, setSubmitting] = useState(false);

  const validate = (): boolean => {
    const newErrors: typeof errors = {};
    if (values.name.trim().length < 2) newErrors.name = 'Name must be at least 2 characters';
    if (values.name.trim().length > 100) newErrors.name = 'Name must be less than 100 characters';
    if (values.description.trim().length === 0) newErrors.description = 'Description is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    (async () => {
      try {
        setSubmitting(true);
        await onSubmit(values);
        // Show success notification using your UI library
        setValues({ name: '', description: '' });
      } catch {
        // Show error notification using your UI library
      } finally {
        setSubmitting(false);
      }
    })();
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-4">
        <div>
          <label htmlFor="name">Project Name</label>
          <input
            id="name"
            type="text"
            value={values.name}
            onChange={(e) => setValues((v) => ({ ...v, name: e.target.value }))}
            placeholder="Enter project name"
            required
          />
          {errors.name && <p className="text-error text-sm">{errors.name}</p>}
        </div>

        <div>
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            value={values.description}
            onChange={(e) => setValues((v) => ({ ...v, description: e.target.value }))}
            placeholder="Describe your project"
            required
            rows={3}
          />
          {errors.description && <p className="text-error text-sm">{errors.description}</p>}
        </div>

        <div className="flex justify-end gap-2">
          {onCancel && (
            <button type="button" onClick={onCancel} className="btn btn-secondary">
              Cancel
            </button>
          )}
          <button type="submit" disabled={submitting} className="btn btn-primary">
            {submitting ? 'Creating...' : 'Create Project'}
          </button>
        </div>
      </div>
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

import { useState } from 'react';

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
  const [values, setValues] = useState<ProjectFormValues>({
    name: '',
    description: '',
    status: 'draft',
    ...initialValues,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof ProjectFormValues, string>>>({});
  const [submitting, setSubmitting] = useState(false);

  const validate = (): boolean => {
    const newErrors: typeof errors = {};
    if (values.name.trim().length < 2) newErrors.name = 'Name must be at least 2 characters';
    if (values.name.trim().length > 100) newErrors.name = 'Name must be under 100 characters';
    if (values.description.trim().length === 0) newErrors.description = 'Description is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    (async () => {
      try {
        setSubmitting(true);
        await onSubmit(values);
      } catch {
        // Show error notification using your UI library
      } finally {
        setSubmitting(false);
      }
    })();
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-4">
        <div>
          <label htmlFor="name">Project Name</label>
          <input
            id="name"
            type="text"
            value={values.name}
            onChange={(e) => setValues((v) => ({ ...v, name: e.target.value }))}
            placeholder="Enter project name"
            required
          />
          {errors.name && <p className="text-error text-sm">{errors.name}</p>}
        </div>

        <div>
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            value={values.description}
            onChange={(e) => setValues((v) => ({ ...v, description: e.target.value }))}
            placeholder="Describe your project"
            required
            rows={3}
          />
          {errors.description && <p className="text-error text-sm">{errors.description}</p>}
        </div>

        <div>
          <label htmlFor="status">Status</label>
          <select
            id="status"
            value={values.status}
            onChange={(e) => setValues((v) => ({ ...v, status: e.target.value as ProjectFormValues['status'] }))}
          >
            <option value="active">Active</option>
            <option value="archived">Archived</option>
            <option value="draft">Draft</option>
          </select>
        </div>

        <div className="flex justify-end gap-2">
          {onCancel && (
            <button type="button" onClick={onCancel} className="btn btn-secondary">
              Cancel
            </button>
          )}
          <button type="submit" disabled={submitting} className="btn btn-primary">
            {submitting ? 'Saving...' : submitLabel}
          </button>
        </div>
      </div>
    </form>
  );
}
```

---

## Example 3: Login Form with Email/Password

```typescript
// src/components/LoginForm.tsx
'use client';

import { useState } from 'react';

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
  const [values, setValues] = useState<LoginFormValues>({ email: '', password: '' });
  const [errors, setErrors] = useState<Partial<Record<keyof LoginFormValues, string>>>({});
  const [submitting, setSubmitting] = useState(false);

  const validate = (): boolean => {
    const newErrors: typeof errors = {};
    if (!/^\S+@\S+\.\S+$/.test(values.email)) newErrors.email = 'Please enter a valid email address';
    if (values.password.length < 8) newErrors.password = 'Password must be at least 8 characters';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    (async () => {
      try {
        setSubmitting(true);
        await onSubmit(values);
      } catch {
        // Show error notification using your UI library
      } finally {
        setSubmitting(false);
      }
    })();
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-4">
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={values.email}
            onChange={(e) => setValues((v) => ({ ...v, email: e.target.value }))}
            placeholder="your@email.com"
            required
          />
          {errors.email && <p className="text-error text-sm">{errors.email}</p>}
        </div>

        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={values.password}
            onChange={(e) => setValues((v) => ({ ...v, password: e.target.value }))}
            placeholder="Enter your password"
            required
          />
          {errors.password && <p className="text-error text-sm">{errors.password}</p>}
        </div>

        {onForgotPassword && (
          <div className="flex justify-end">
            <button type="button" onClick={onForgotPassword} className="text-sm text-blue-600 hover:underline">
              Forgot password?
            </button>
          </div>
        )}

        <button type="submit" disabled={submitting} className="btn btn-primary w-full">
          {submitting ? 'Signing in...' : 'Sign In'}
        </button>
      </div>
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

type OnboardingFormValues = {
  name: string;
  email: string;
  company: string;
  role: string;
  bio: string;
};

type OnboardingFormProps = {
  onSubmit: (values: OnboardingFormValues) => Promise<void>;
};

/** Multi-step onboarding form */
export function OnboardingForm({ onSubmit }: OnboardingFormProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [values, setValues] = useState<OnboardingFormValues>({
    name: '', email: '', company: '', role: '', bio: '',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof OnboardingFormValues, string>>>({});
  const [submitting, setSubmitting] = useState(false);

  const validateStep = (step: number): boolean => {
    const newErrors: typeof errors = {};
    if (step === 0) {
      if (values.name.trim().length < 2) newErrors.name = 'Name is required';
      if (!/^\S+@\S+\.\S+$/.test(values.email)) newErrors.email = 'Invalid email';
    }
    if (step === 1) {
      if (values.company.trim().length < 1) newErrors.company = 'Company is required';
      if (!values.role) newErrors.role = 'Please select a role';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prev) => Math.min(prev + 1, 2));
    }
  };

  const prevStep = () => setActiveStep((prev) => Math.max(prev - 1, 0));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    (async () => {
      try {
        setSubmitting(true);
        await onSubmit(values);
        // Show success notification using your UI library
      } catch {
        // Show error notification using your UI library
      } finally {
        setSubmitting(false);
      }
    })();
  };

  const updateValue = (field: keyof OnboardingFormValues, value: string) => {
    setValues((v) => ({ ...v, [field]: value }));
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Step indicators */}
      <div className="flex gap-4 mb-6">
        {['Personal', 'Work', 'Profile'].map((label, i) => (
          <span key={label} className={`text-sm ${i <= activeStep ? 'font-bold' : 'text-gray-400'}`}>
            {i + 1}. {label}
          </span>
        ))}
      </div>

      {/* Step 1: Personal */}
      {activeStep === 0 && (
        <div className="space-y-4">
          <div>
            <label htmlFor="name">Name</label>
            <input id="name" value={values.name} onChange={(e) => updateValue('name', e.target.value)} required />
            {errors.name && <p className="text-error text-sm">{errors.name}</p>}
          </div>
          <div>
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={values.email} onChange={(e) => updateValue('email', e.target.value)} required />
            {errors.email && <p className="text-error text-sm">{errors.email}</p>}
          </div>
        </div>
      )}

      {/* Step 2: Work */}
      {activeStep === 1 && (
        <div className="space-y-4">
          <div>
            <label htmlFor="company">Company</label>
            <input id="company" value={values.company} onChange={(e) => updateValue('company', e.target.value)} required />
            {errors.company && <p className="text-error text-sm">{errors.company}</p>}
          </div>
          <div>
            <label htmlFor="role">Role</label>
            <select id="role" value={values.role} onChange={(e) => updateValue('role', e.target.value)} required>
              <option value="">Select a role</option>
              <option value="Developer">Developer</option>
              <option value="Designer">Designer</option>
              <option value="Manager">Manager</option>
              <option value="Other">Other</option>
            </select>
            {errors.role && <p className="text-error text-sm">{errors.role}</p>}
          </div>
        </div>
      )}

      {/* Step 3: Profile */}
      {activeStep === 2 && (
        <div className="space-y-4">
          <div>
            <label htmlFor="bio">Bio</label>
            <textarea id="bio" value={values.bio} onChange={(e) => updateValue('bio', e.target.value)} rows={4} placeholder="Tell us about yourself" />
          </div>
        </div>
      )}

      <div className="flex justify-end gap-2 mt-6">
        {activeStep > 0 && (
          <button type="button" onClick={prevStep} className="btn btn-secondary">Back</button>
        )}
        {activeStep < 2 ? (
          <button type="button" onClick={nextStep} className="btn btn-primary">Next</button>
        ) : (
          <button type="submit" disabled={submitting} className="btn btn-primary">
            {submitting ? 'Completing...' : 'Complete Setup'}
          </button>
        )}
      </div>
    </form>
  );
}
```

---

## Form Validation Rules Reference

```typescript
// Common validation patterns (adapt to your form library)

const validationRules = {
  // Required string
  required: (value: string) => value.trim().length === 0 ? 'Required' : null,

  // Minimum length
  minLength: (min: number) => (value: string) =>
    value.trim().length < min ? `At least ${min} characters` : null,

  // Maximum length
  maxLength: (max: number) => (value: string) =>
    value.length > max ? `Must be under ${max} characters` : null,

  // Email format
  email: (value: string) =>
    /^\S+@\S+\.\S+$/.test(value) ? null : 'Invalid email',

  // Password strength
  password: (value: string) => {
    if (value.length < 8) return 'At least 8 characters';
    if (!/[A-Z]/.test(value)) return 'Must contain uppercase letter';
    if (!/[0-9]/.test(value)) return 'Must contain number';
    return null;
  },

  // URL format
  url: (value: string) => {
    if (!value) return null; // Optional
    try { new URL(value); return null; } catch { return 'Invalid URL'; }
  },

  // Number range
  numberRange: (min: number, max: number) => (value: number) =>
    value < min || value > max ? `Must be between ${min} and ${max}` : null,

  // Select required
  selectRequired: (value: string) => value ? null : 'Please select an option',

  // Array minimum items
  arrayMin: (min: number) => (value: unknown[]) =>
    value.length < min ? `At least ${min} item(s) required` : null,
};
```
