# TypeScript + React + Next.js Style Guide

Style conventions for all TypeScript code in this React + Next.js application.
These rules are enforced by ESLint, TypeScript strict mode, and Prettier. All
agents must follow these conventions when generating or modifying code.

---

## 1. TypeScript Strict Mode

Enable `strict: true` in `tsconfig.json`. This includes:

- `noImplicitAny` -- every value must have a known type
- `strictNullChecks` -- `null` and `undefined` are distinct types
- `strictFunctionTypes` -- function parameter types are checked correctly

**Never use `any`.** Use `unknown` and narrow with type guards:

```typescript
// CORRECT
function processValue(value: unknown): string {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  throw new Error('Unexpected value type');
}

// CORRECT - type guard function
function isApiError(error: unknown): error is { message: string; code: number } {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    'code' in error
  );
}

// WRONG
function processValue(value: any): string {
  return value.toString(); // unsafe
}
```

---

## 2. `type` vs `interface`

Use `type` for component props and data shapes. Reserve `interface` only when
declaration merging is needed (rare).

```typescript
// CORRECT
type ProjectCardProps = {
  name: string;
  description: string;
  status: 'active' | 'archived' | 'draft';
};

type CreateProjectPayload = {
  name: string;
  description: string;
};

// WRONG - do not use interface for props or data shapes
interface ProjectCardProps {
  name: string;
}
```

Use union types or `as const` objects instead of enums:

```typescript
// CORRECT
type Status = 'active' | 'archived' | 'draft';

const STATUS = {
  ACTIVE: 'active',
  ARCHIVED: 'archived',
  DRAFT: 'draft',
} as const;

// WRONG
enum Status {
  Active = 'active',
  Archived = 'archived',
}
```

---

## 3. Naming Conventions

| Entity | Convention | Example |
|---|---|---|
| Component | PascalCase | `ProjectCard`, `CreateProjectForm` |
| Component file | PascalCase.tsx | `ProjectCard.tsx` |
| Container | PascalCase + `Container` suffix | `ProjectListContainer` |
| Service function | camelCase + `Api` suffix | `fetchProjectsApi`, `createProjectApi` |
| Service file | camelCase.ts | `projects.ts` |
| Context | PascalCase + `Context` | `AuthContext` |
| Custom hook | camelCase + `use` prefix | `useAuth`, `useProjects` |
| Hook file | camelCase.ts | `useAuth.ts` |
| Type | PascalCase | `Project`, `CreateProjectPayload` |
| Type file | camelCase.ts | `project.ts` |
| Constant | SCREAMING_SNAKE_CASE | `MAX_PAGE_SIZE`, `API_BASE_URL` |
| Test file | Same as source + `.test.tsx` | `ProjectCard.test.tsx` |
| Page file | `page.tsx` in route dir | `src/app/projects/page.tsx` |
| Layout file | `layout.tsx` in route dir | `src/app/layout.tsx` |

---

## 4. Import Organization

Imports are grouped in four sections, separated by blank lines:

1. **React / Next.js** -- `react`, `next/link`, `next/image`, `next/navigation`
2. **Third-party** -- `@mantine/core`, `@mantine/form`, `@mantine/notifications`
3. **Internal (absolute)** -- `@/services/*`, `@/contexts/*`, `@/components/*`
4. **Relative** -- `./utils`, `./helpers` (only for co-located files)

```typescript
// 1. React / Next.js
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';

// 2. Third-party
import { Button, TextInput, Stack, Group } from '@mantine/core';
import { useForm } from '@mantine/form';
import { showNotification } from '@mantine/notifications';

// 3. Internal (absolute imports via @/)
import { fetchProjectsApi } from '@/services/projects';
import { useAuth } from '@/contexts/AuthContext';
import { ProjectCard } from '@/components/ProjectCard';

// 4. Relative (only for co-located files)
import { formatDate } from './utils';
```

Use absolute imports via `@/` mapped to `src/` for all internal modules.
Only use relative imports for co-located helper files.

---

## 5. `'use client'` Directive Rules

All components are **Server Components by default**. Only add `'use client'` when
the component uses:

- React hooks (`useState`, `useEffect`, `useForm`, `useContext`)
- Event handlers (`onClick`, `onSubmit`, `onChange`)
- Browser APIs (`window`, `document`, `localStorage`)
- Third-party client-only libraries

```typescript
// Server Component (default) -- no directive needed
import { Text, Card } from '@mantine/core';

type ProjectCardProps = {
  name: string;
  description: string;
};

export function ProjectCard({ name, description }: ProjectCardProps) {
  return (
    <Card shadow="sm" padding="lg">
      <Text fw={500}>{name}</Text>
      <Text size="sm" c="dimmed">{description}</Text>
    </Card>
  );
}
```

```typescript
// Client Component -- needs hooks and event handlers
'use client';

import { useState } from 'react';
import { Button } from '@mantine/core';

export function Counter() {
  const [count, setCount] = useState(0);
  return <Button onClick={() => setCount((c) => c + 1)}>{count}</Button>;
}
```

| Needs... | `'use client'`? |
|---|---|
| Just displaying props data | No (Server Component) |
| Mantine layout components only (`Card`, `Stack`, `Text`) | No |
| `useState`, `useEffect`, `useForm` | Yes |
| `onClick`, `onChange`, `onSubmit` | Yes |
| `useRouter()` from `next/navigation` | Yes |
| `useSearchParams()` | Yes |
| `window`, `document`, `localStorage` | Yes |
| Third-party hook library | Yes |
| Static data fetching with `fetch()` in component body | No |

---

## 6. Named Exports

Use **named exports** for all components, services, hooks, and contexts. The only
exception is page files, which must use default exports (Next.js requirement).

```typescript
// CORRECT - named export
export function ProjectCard({ name }: ProjectCardProps) { ... }
export function useAuth() { ... }
export const fetchProjectsApi = () => ...;

// CORRECT - default export for pages only (Next.js requirement)
// src/app/projects/page.tsx
export default function ProjectsPage() { ... }

// WRONG - default export for non-page files
export default function ProjectCard() { ... }
```

---

## 7. Component Prop Patterns

Destructure props in the function signature. Use the `onAction` naming convention
for callback props:

```typescript
type ProjectCardProps = {
  project: Project;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  isSelected?: boolean;
};

// CORRECT - destructure in signature
export function ProjectCard({
  project,
  onEdit,
  onDelete,
  isSelected = false,
}: ProjectCardProps) {
  return (
    <Card shadow={isSelected ? 'md' : 'sm'}>
      <Text>{project.name}</Text>
      <Group>
        <Button onClick={() => onEdit(project.id)}>Edit</Button>
        <Button color="red" onClick={() => onDelete(project.id)}>Delete</Button>
      </Group>
    </Card>
  );
}

// WRONG - accessing props.field
export function ProjectCard(props: ProjectCardProps) {
  return <Text>{props.project.name}</Text>;
}
```

Callback props:
- Prefix with `on`: `onClick`, `onSubmit`, `onDelete`, `onEdit`
- Boolean props: prefix with `is`, `has`, or `should`: `isSelected`, `hasError`, `shouldAnimate`

---

## 8. Null and Undefined Handling

Use optional chaining (`?.`) and nullish coalescing (`??`) instead of manual checks.
Never use the non-null assertion operator (`!`).

```typescript
// CORRECT
const name = user?.profile?.name ?? 'Unknown';
const items = response?.data ?? [];

// CORRECT - type narrowing
if (error instanceof Error) {
  setMessage(error.message);
} else {
  setMessage('An unknown error occurred');
}

// WRONG - non-null assertion
const name = user!.profile!.name;

// WRONG - manual null checks when optional chaining works
const name = user && user.profile && user.profile.name ? user.profile.name : 'Unknown';
```

---

## 9. Async Patterns

Use the IIFE (Immediately Invoked Function Expression) async pattern inside
`useEffect` and `onSubmit` handlers:

```typescript
// useEffect with async data fetching
useEffect(() => {
  (async () => {
    try {
      setLoading(true);
      const data = await fetchProjectsApi();
      setProjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  })();
}, []);

// Form submission with IIFE async
const handleSubmit = form.onSubmit((values) => {
  (async () => {
    try {
      await createProjectApi(values);
      showNotification({ title: 'Success', message: 'Created', color: 'green' });
      form.reset();
    } catch {
      showNotification({ title: 'Error', message: 'Failed', color: 'red' });
    }
  })();
});
```

Always use `try/catch/finally`:
- `try`: the async operation
- `catch`: error handling (set error state or show notification)
- `finally`: cleanup (set loading to false)

---

## 10. Mantine UI Usage

Use Mantine components for all UI elements. Never use raw HTML when a Mantine
equivalent exists.

| Raw HTML | Mantine Replacement |
|---|---|
| `<div>` with flex | `<Group>`, `<Stack>`, `<Flex>` |
| `<button>` | `<Button>` |
| `<input>` | `<TextInput>`, `<NumberInput>`, `<Select>` |
| `<textarea>` | `<Textarea>` |
| `<table>` | `<Table>` |
| `<a>` | `<Anchor>` or Next.js `<Link>` |
| `<h1>` - `<h6>` | `<Title order={n}>` |
| `<p>` | `<Text>` |
| `<img>` | Next.js `<Image>` |
| `<dialog>` / `<div>` modal | `<Modal>` |
| `<ul>` / `<ol>` | `<List>` |
| `<select>` | `<Select>` or `<NativeSelect>` |
| Custom spinner | `<LoadingOverlay>` or `<Loader>` |
| Custom alert | `<Alert>` |
| Custom card | `<Card>` |

Use `@mantine/form` for form state and `@mantine/notifications` for user feedback:

```typescript
// Form state
const form = useForm({
  initialValues: { name: '', email: '' },
  validate: {
    name: (value) => (value.trim().length < 2 ? 'Name too short' : null),
    email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
  },
});

// User feedback
showNotification({ title: 'Success', message: 'Saved', color: 'green' });
showNotification({ title: 'Error', message: 'Failed', color: 'red' });
```

---

## 11. Error Handling

Always handle three states for async operations: **loading**, **error**, and
**success**.

```typescript
// Container with loading/error/success states
const [data, setData] = useState<Project[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);

useEffect(() => {
  (async () => {
    try {
      const result = await fetchProjectsApi();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  })();
}, []);

if (loading) return <LoadingOverlay visible />;
if (error) return <Alert color="red" title="Error">{error}</Alert>;
```

For form submissions, use `showNotification` for feedback:

```typescript
try {
  await createProjectApi(values);
  showNotification({ title: 'Success', message: 'Project created', color: 'green' });
} catch {
  showNotification({ title: 'Error', message: 'Failed to create project', color: 'red' });
}
```

---

## 12. Formatting and Line Length

Formatting is handled by Prettier. Do not manually format code.

| Setting | Value |
|---|---|
| Print width | 100 |
| Tab width | 2 (spaces) |
| Quotes | Single quotes |
| Semicolons | Yes |
| Trailing commas | `all` |
| Bracket spacing | Yes |
| JSX quotes | Double quotes |
| Arrow function parens | `always` |

```bash
# Format all files
npx prettier --write "src/**/*.{ts,tsx}"

# Check formatting
npx prettier --check "src/**/*.{ts,tsx}"
```

---

## 13. React Context Conventions

Contexts follow a strict pattern: `undefined` default, Provider component,
custom hook that throws outside Provider.

```typescript
'use client';

import { createContext, useContext, useState, useMemo, useCallback, type ReactNode } from 'react';

type AuthContextValue = {
  user: User | null;
  isAuthenticated: boolean;
  login: (credentials: Credentials) => Promise<void>;
  logout: () => void;
};

// 1. Create with undefined default
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// 2. Provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = useCallback(async (credentials: Credentials) => {
    const response = await loginApi(credentials);
    setUser(response.user);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
  }, []);

  // useMemo on value to prevent unnecessary re-renders
  const value = useMemo(
    () => ({ user, isAuthenticated: user !== null, login, logout }),
    [user, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// 3. Custom hook that throws if used outside Provider
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

Key rules:
- `createContext<T | undefined>(undefined)` -- always `undefined` as default
- `useMemo` on the value object to prevent re-renders
- `useCallback` on handlers to stabilize function references
- Custom hook throws a descriptive error if used outside the Provider

---

## 14. ESLint and Prettier Enforcement

These rules are enforced by ESLint and Prettier. Run before every commit:

```bash
# Type checking
npx tsc --noEmit

# Linting
npm run lint

# Formatting
npx prettier --write "src/**/*.{ts,tsx}"
```

Key ESLint rules:
- `@typescript-eslint/no-explicit-any` -- disallow `any`
- `@typescript-eslint/no-non-null-assertion` -- disallow `!` operator
- `react-hooks/rules-of-hooks` -- enforce rules of hooks
- `react-hooks/exhaustive-deps` -- enforce correct dependency arrays
- `@next/next/no-img-element` -- use `next/image` instead
- `import/order` -- enforce import grouping

All three commands must pass with zero errors before code is considered complete.
