# React + Next.js Stack Conventions

## Project Structure

This project uses Next.js with the App Router. All source code lives under `src/`.

```
src/
  app/                  # Next.js App Router pages and layouts
    (auth)/             # Route groups for authentication pages
    api/                # API routes (route handlers)
    layout.tsx          # Root layout
    page.tsx            # Root page
  components/           # Presentational (UI) components
  containers/           # Data-fetching + state management wrappers
  services/             # API service modules (HTTP client wrappers)
  contexts/             # React Context providers and hooks
  hooks/                # Custom React hooks
  utils/                # Utility functions
  types/                # Shared TypeScript type definitions
  styles/               # Global styles and theme configuration
```

## Core Principles

### Server Components by Default

All components are React Server Components unless they need client-side
interactivity. Add `'use client'` only when the component uses:

- React hooks (`useState`, `useEffect`, `useForm`, etc.)
- Event handlers (`onClick`, `onSubmit`, `onChange`, etc.)
- Browser APIs (`window`, `document`, `localStorage`, etc.)
- Third-party client-only libraries

### Page -> Container -> Component Pattern

- **Pages** (`src/app/**/page.tsx`): Minimal. Define metadata, delegate to a container.
- **Containers** (`src/containers/`): Fetch data, manage state, handle events. Pass data down to components.
- **Components** (`src/components/`): Presentational only. Receive data via props, render UI with Mantine.

### TypeScript Strict Mode

- Use `type` for component props (not `interface`)
- No `any` types -- use `unknown` and narrow with type guards
- All function return types should be inferable or explicitly annotated
- Enable `strict: true` in `tsconfig.json`

## UI Framework: Mantine v7+

- Use Mantine components for all UI: `Button`, `TextInput`, `Select`, `Modal`, `Card`, `Stack`, `Group`, etc.
- Use `@mantine/notifications` with `showNotification()` for user feedback
- Use `@mantine/form` with `useForm()` for form state and validation
- Theme customizations go in `src/styles/theme.ts`
- Do NOT use raw HTML elements when a Mantine equivalent exists

## API Service Pattern

All HTTP calls go through typed service modules in `src/services/`.

```typescript
// src/services/request.ts - Base request wrapper
async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
```

Service files use the `Api` suffix for exported functions:

```typescript
// src/services/projects.ts
export const fetchProjectsApi = () => request<Project[]>('/api/projects');
export const fetchProjectApi = (id: string) => request<Project>(`/api/projects/${id}`);
export const createProjectApi = (data: CreateProjectPayload) =>
  request<Project>('/api/projects', { method: 'POST', body: JSON.stringify(data) });
```

## Form Pattern

Forms use `@mantine/form` with validation and async submission via IIFE:

```typescript
'use client';

import { useForm } from '@mantine/form';
import { showNotification } from '@mantine/notifications';

const form = useForm({
  initialValues: { name: '', email: '' },
  validate: {
    name: (value) => (value.trim().length < 2 ? 'Name is too short' : null),
    email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
  },
});

const handleSubmit = form.onSubmit((values) => {
  (async () => {
    try {
      await createItemApi(values);
      showNotification({ title: 'Success', message: 'Item created', color: 'green' });
    } catch (error) {
      showNotification({ title: 'Error', message: 'Failed to create item', color: 'red' });
    }
  })();
});
```

## Context Pattern

Contexts follow Provider + custom hook with undefined safety check:

```typescript
'use client';

import { createContext, useContext, useState, useMemo, useCallback, type ReactNode } from 'react';

type AuthContextValue = {
  user: User | null;
  login: (credentials: Credentials) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = useCallback(async (credentials: Credentials) => {
    const user = await loginApi(credentials);
    setUser(user);
  }, []);

  const value = useMemo(() => ({ user, login, logout }), [user, login, logout]);

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

## Container Pattern

Containers fetch data using `useEffect` with IIFE async pattern:

```typescript
'use client';

import { useState, useEffect } from 'react';

export function ProjectListContainer() {
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

  if (loading) return <LoadingOverlay visible />;
  if (error) return <Alert color="red">{error}</Alert>;

  return <ProjectList projects={projects} />;
}
```

## Development Commands

```bash
# Linting
npm run lint

# Type checking
npx tsc --noEmit

# Run tests
npm test

# Run a specific test file
npx jest path/to/file.test.tsx

# Build
npm run build

# Dev server
npm run dev

# Format code
npx prettier --write "src/**/*.{ts,tsx}"
```

## File Naming Conventions

- Components: `PascalCase.tsx` (e.g., `ProjectCard.tsx`)
- Containers: `PascalCase.tsx` with `Container` suffix (e.g., `ProjectListContainer.tsx`)
- Services: `camelCase.ts` (e.g., `projects.ts`)
- Contexts: `PascalCase.tsx` with `Context` in name (e.g., `AuthContext.tsx`)
- Hooks: `camelCase.ts` with `use` prefix (e.g., `useProjects.ts`)
- Types: `camelCase.ts` (e.g., `project.ts`)
- Tests: Same name as source with `.test.tsx` suffix (e.g., `ProjectCard.test.tsx`)
- Pages: `page.tsx` inside route directories (Next.js App Router convention)

## Import Conventions

- Use absolute imports via `@/` alias mapped to `src/`
- Group imports in order: React/Next, third-party, internal (`@/`), relative
- Use named exports (not default exports) for components, services, and hooks
- Pages may use default exports as required by Next.js
