# React / Next.js Code Patterns

Reference patterns for code generation based on Sharebird's frontend conventions.
All agents and skills should follow these patterns when generating code.

---

## Pattern 1: Client Component with Form

A client-side component using `@mantine/form`, IIFE async submission, and
`showNotification` for user feedback.

```typescript
'use client';

import { useForm } from '@mantine/form';
import { TextInput, Textarea, Button, Stack, Group } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { createProjectApi } from '@/services/projects';

type CreateProjectFormValues = {
  name: string;
  description: string;
};

type CreateProjectFormProps = {
  onSuccess?: () => void;
  onCancel?: () => void;
};

export function CreateProjectForm({ onSuccess, onCancel }: CreateProjectFormProps) {
  const form = useForm<CreateProjectFormValues>({
    initialValues: {
      name: '',
      description: '',
    },
    validate: {
      name: (value) =>
        value.trim().length < 2 ? 'Name must be at least 2 characters' : null,
      description: (value) =>
        value.trim().length === 0 ? 'Description is required' : null,
    },
  });

  const handleSubmit = form.onSubmit((values) => {
    (async () => {
      try {
        await createProjectApi(values);
        showNotification({
          title: 'Success',
          message: 'Project created successfully',
          color: 'green',
        });
        form.reset();
        onSuccess?.();
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

### Key Points

- `'use client'` because it uses `useForm` hook and event handlers
- `type` for props and form values (not `interface`)
- IIFE async `(() => { ... })()` inside `form.onSubmit` callback
- `showNotification` for success and error feedback
- `form.getInputProps('field')` to wire up Mantine inputs
- `form.reset()` on success

---

## Pattern 2: Container with Data Fetching

A container component that fetches data, manages state, and delegates rendering
to a presentational component.

```typescript
'use client';

import { useState, useEffect, useCallback } from 'react';
import { LoadingOverlay, Alert, Stack, Title, Group, Button } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { useRouter } from 'next/navigation';
import { fetchProjectsApi, deleteProjectApi } from '@/services/projects';
import { ProjectList } from '@/components/ProjectList';

type Project = {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'archived' | 'draft';
  updatedAt: string;
};

export function ProjectListContainer() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchProjectsApi();
        setProjects(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load projects');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleDelete = useCallback(async (id: string) => {
    try {
      await deleteProjectApi(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
      showNotification({
        title: 'Deleted',
        message: 'Project removed successfully',
        color: 'green',
      });
    } catch {
      showNotification({
        title: 'Error',
        message: 'Failed to delete project',
        color: 'red',
      });
    }
  }, []);

  if (loading) return <LoadingOverlay visible />;
  if (error) return <Alert color="red" title="Error">{error}</Alert>;

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Projects</Title>
        <Button onClick={() => router.push('/projects/new')}>New Project</Button>
      </Group>
      <ProjectList projects={projects} onDelete={handleDelete} />
    </Stack>
  );
}
```

### Key Points

- `'use client'` because it uses hooks and event handlers
- IIFE async pattern in `useEffect`: `(async () => { ... })()`
- Three state variables: `data`, `loading`, `error`
- `try/catch/finally` with `setLoading(false)` in `finally`
- `useCallback` for event handlers passed to children
- Renders `LoadingOverlay` while loading, `Alert` on error
- Delegates rendering to `ProjectList` presentational component

---

## Pattern 3: Page with Metadata

A Next.js App Router page that defines metadata and delegates to a container.

```typescript
// src/app/projects/page.tsx
import { Metadata } from 'next';
import { ProjectListContainer } from '@/containers/ProjectListContainer';

export const metadata: Metadata = {
  title: 'Projects',
  description: 'View and manage your projects',
};

export default function ProjectsPage() {
  return <ProjectListContainer />;
}
```

### Dynamic Route Page

```typescript
// src/app/projects/[id]/page.tsx
import { Metadata } from 'next';
import { ProjectDetailContainer } from '@/containers/ProjectDetailContainer';

type PageProps = {
  params: { id: string };
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  return {
    title: `Project ${params.id}`,
  };
}

export default function ProjectDetailPage({ params }: PageProps) {
  return <ProjectDetailContainer id={params.id} />;
}
```

### Key Points

- Pages are Server Components (no `'use client'`)
- Pages define `metadata` or `generateMetadata` for SEO
- Pages delegate to containers, never fetch data themselves (unless using server-side fetch)
- Pages use default exports (Next.js requirement)
- Dynamic routes type `params` with `type PageProps`

---

## Pattern 4: Layout with Providers

Root layout wrapping the app with theme, notification, and context providers.

```typescript
// src/app/layout.tsx
import { MantineProvider, ColorSchemeScript } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { AuthProvider } from '@/contexts/AuthContext';
import { theme } from '@/styles/theme';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';

export const metadata = {
  title: { default: 'My App', template: '%s | My App' },
  description: 'Application description',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <ColorSchemeScript />
      </head>
      <body>
        <MantineProvider theme={theme}>
          <Notifications position="top-right" />
          <AuthProvider>{children}</AuthProvider>
        </MantineProvider>
      </body>
    </html>
  );
}
```

### Key Points

- Root layout is a Server Component
- `ColorSchemeScript` prevents flash of unstyled content
- `MantineProvider` wraps entire app
- `Notifications` component enables `showNotification` everywhere
- Context providers nested inside MantineProvider
- CSS imports for Mantine at the layout level

---

## Pattern 5: API Service

Typed service module using the `request<T>()` wrapper.

```typescript
// src/services/request.ts
export async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
```

```typescript
// src/services/projects.ts
import { request } from './request';

type Project = {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'archived' | 'draft';
  createdAt: string;
  updatedAt: string;
};

type CreateProjectPayload = {
  name: string;
  description: string;
};

export const fetchProjectsApi = () =>
  request<Project[]>('/api/projects');

export const fetchProjectApi = (id: string) =>
  request<Project>(`/api/projects/${id}`);

export const createProjectApi = (data: CreateProjectPayload) =>
  request<Project>('/api/projects', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const updateProjectApi = (id: string, data: Partial<CreateProjectPayload>) =>
  request<Project>(`/api/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

export const deleteProjectApi = (id: string) =>
  request<void>(`/api/projects/${id}`, { method: 'DELETE' });
```

### Key Points

- `request<T>()` generic wrapper for type-safe API calls
- Function names use `Api` suffix: `fetchProjectsApi`, `createProjectApi`
- Response types and payload types defined with `type`
- Named exports only (no default export)
- Error thrown for non-OK responses

---

## Pattern 6: React Context

Context with Provider, `useMemo` value, and custom hook with safety check.

```typescript
// src/contexts/AuthContext.tsx
'use client';

import {
  createContext,
  useContext,
  useState,
  useMemo,
  useCallback,
  type ReactNode,
} from 'react';

type User = {
  id: string;
  name: string;
  email: string;
};

type AuthContextValue = {
  user: User | null;
  isAuthenticated: boolean;
  login: (credentials: { email: string; password: string }) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = useCallback(async (credentials: { email: string; password: string }) => {
    const response = await loginApi(credentials);
    setUser(response.user);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      login,
      logout,
    }),
    [user, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### Key Points

- `createContext<T | undefined>(undefined)` -- undefined as default
- Custom hook `useAuth()` throws if used outside Provider
- `useMemo` on the value object to prevent unnecessary re-renders
- `useCallback` on handlers to stabilize function references
- `type` for context value (not `interface`)

---

## Pattern 7: Mantine Form with Validation

Complete form pattern with field-level validation.

```typescript
const form = useForm({
  initialValues: {
    name: '',
    email: '',
    role: '' as 'admin' | 'member' | 'viewer' | '',
  },
  validate: {
    name: (value) => {
      if (value.trim().length < 2) return 'Name must be at least 2 characters';
      if (value.trim().length > 100) return 'Name is too long';
      return null;
    },
    email: (value) =>
      /^\S+@\S+\.\S+$/.test(value) ? null : 'Invalid email',
    role: (value) =>
      value ? null : 'Please select a role',
  },
});

// Wire up inputs
<TextInput label="Name" {...form.getInputProps('name')} />
<TextInput label="Email" {...form.getInputProps('email')} />
<Select
  label="Role"
  data={['admin', 'member', 'viewer']}
  {...form.getInputProps('role')}
/>

// Handle submission
const handleSubmit = form.onSubmit((values) => {
  (async () => {
    try {
      await submitApi(values);
      showNotification({ title: 'Success', message: 'Saved', color: 'green' });
    } catch {
      showNotification({ title: 'Error', message: 'Failed', color: 'red' });
    }
  })();
});
```

### Key Points

- `useForm` with typed initial values
- `validate` returns `null` for valid, error string for invalid
- `form.getInputProps('field')` wires value, onChange, and error
- `form.onSubmit` validates before calling the callback
- IIFE async for the submission handler

---

## Quick Reference: When to Use 'use client'

| Needs... | 'use client'? |
|---|---|
| Just displaying props data | No (Server Component) |
| Mantine layout components only (Card, Stack, Text) | No |
| `useState`, `useEffect`, `useForm` | Yes |
| `onClick`, `onChange`, `onSubmit` | Yes |
| `useRouter()` from next/navigation | Yes |
| `useSearchParams()` | Yes |
| `window`, `document`, `localStorage` | Yes |
| Third-party hook library | Yes |
| Static data fetching with `fetch()` in component body | No |
