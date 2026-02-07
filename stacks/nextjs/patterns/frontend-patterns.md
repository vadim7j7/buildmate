# React / Next.js Code Patterns

Reference patterns for code generation following Next.js App Router conventions.
**Server Components are the default.** Only use Client Components when necessary.

---

## Pattern 1: Page with Server-Side Data Fetching (DEFAULT)

The primary pattern. Pages are async Server Components that fetch data directly.

```typescript
// src/app/projects/page.tsx
import { Metadata } from 'next';
import { Stack, Title } from '@mantine/core';
import { getProjects } from '@/lib/data/projects';
import { ProjectList } from '@/components/projects/ProjectList';
import { CreateProjectButton } from '@/components/projects/CreateProjectButton';

export const metadata: Metadata = {
  title: 'Projects',
  description: 'View and manage your projects',
};

export default async function ProjectsPage() {
  const projects = await getProjects();

  return (
    <Stack gap="lg">
      <Title order={1}>Projects</Title>
      <CreateProjectButton />
      <ProjectList projects={projects} />
    </Stack>
  );
}
```

### Key Points

- Page is an **async Server Component** (no `'use client'`)
- Data fetched directly in the component body with `await`
- No `useState`, no `useEffect`, no loading states needed
- `metadata` export for SEO (only works in Server Components)
- Child components receive data as props
- Fast initial page load with SSR

---

## Pattern 2: Data Fetching Layer

Server-side data fetching functions in `lib/data/`. These run on the server only.

```typescript
// src/lib/data/projects.ts
import { db } from '@/lib/db';
import { cache } from 'react';

export type Project = {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'archived' | 'draft';
  createdAt: Date;
  updatedAt: Date;
};

// Cached and deduplicated automatically by React
export const getProjects = cache(async (): Promise<Project[]> => {
  return db.project.findMany({
    orderBy: { updatedAt: 'desc' },
  });
});

export const getProject = cache(async (id: string): Promise<Project | null> => {
  return db.project.findUnique({
    where: { id },
  });
});

// For external APIs
export async function getProjectsFromApi(): Promise<Project[]> {
  const response = await fetch(`${process.env.API_URL}/projects`, {
    next: { revalidate: 60 }, // Cache for 60 seconds
  });

  if (!response.ok) {
    throw new Error('Failed to fetch projects');
  }

  return response.json();
}
```

### Key Points

- Functions in `lib/data/` run on the server only
- Use `cache()` from React to deduplicate requests
- Use `next: { revalidate: N }` for time-based caching
- Use `next: { tags: ['projects'] }` for on-demand revalidation
- Direct database access or external API calls
- Types exported for use in components

---

## Pattern 3: Server Component (Presentational)

Server Components that receive data as props. No `'use client'` needed.

```typescript
// src/components/projects/ProjectList.tsx
import { Stack, Text } from '@mantine/core';
import { ProjectCard } from './ProjectCard';
import type { Project } from '@/lib/data/projects';

type ProjectListProps = {
  projects: Project[];
};

export function ProjectList({ projects }: ProjectListProps) {
  if (projects.length === 0) {
    return <Text c="dimmed">No projects yet. Create your first project!</Text>;
  }

  return (
    <Stack gap="md">
      {projects.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </Stack>
  );
}
```

```typescript
// src/components/projects/ProjectCard.tsx
import { Card, Text, Badge, Group } from '@mantine/core';
import Link from 'next/link';
import { DeleteProjectButton } from './DeleteProjectButton';
import type { Project } from '@/lib/data/projects';

type ProjectCardProps = {
  project: Project;
};

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Card shadow="sm" padding="lg" component={Link} href={`/projects/${project.id}`}>
      <Group justify="space-between" align="flex-start">
        <div>
          <Text fw={500}>{project.name}</Text>
          <Text size="sm" c="dimmed" mt="xs">
            {project.description}
          </Text>
        </div>
        <Group gap="xs">
          <Badge color={project.status === 'active' ? 'green' : 'gray'}>
            {project.status}
          </Badge>
          <DeleteProjectButton projectId={project.id} />
        </Group>
      </Group>
    </Card>
  );
}
```

### Key Points

- No `'use client'` directive
- Pure presentational components receiving props
- Can use Mantine components (they work in Server Components)
- Can use Next.js `Link` for navigation
- Interactive children (buttons) are separate Client Components

---

## Pattern 4: Server Actions for Mutations

Use Server Actions for create, update, delete operations. No API routes needed.

```typescript
// src/lib/actions/projects.ts
'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { db } from '@/lib/db';
import { z } from 'zod';

const CreateProjectSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  description: z.string().min(1, 'Description is required'),
});

export type ActionState = {
  success: boolean;
  message: string;
  errors?: Record<string, string[]>;
};

export async function createProject(
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const parsed = CreateProjectSchema.safeParse({
    name: formData.get('name'),
    description: formData.get('description'),
  });

  if (!parsed.success) {
    return {
      success: false,
      message: 'Validation failed',
      errors: parsed.error.flatten().fieldErrors,
    };
  }

  try {
    await db.project.create({
      data: parsed.data,
    });
  } catch {
    return {
      success: false,
      message: 'Failed to create project',
    };
  }

  revalidatePath('/projects');
  redirect('/projects');
}

export async function deleteProject(projectId: string): Promise<ActionState> {
  try {
    await db.project.delete({
      where: { id: projectId },
    });

    revalidatePath('/projects');

    return { success: true, message: 'Project deleted' };
  } catch {
    return { success: false, message: 'Failed to delete project' };
  }
}
```

### Key Points

- `'use server'` directive at the top of the file
- Functions can be called directly from Client Components
- Use `revalidatePath()` to refresh cached data after mutations
- Use `redirect()` for navigation after successful mutations
- Zod for validation with typed error responses
- Return `ActionState` for client feedback

---

## Pattern 5: Client Component with Server Action

Client Components for interactivity, using Server Actions for mutations.

```typescript
// src/components/projects/CreateProjectButton.tsx
'use client';

import { useState } from 'react';
import { Button, Modal } from '@mantine/core';
import { CreateProjectForm } from './CreateProjectForm';

export function CreateProjectButton() {
  const [opened, setOpened] = useState(false);

  return (
    <>
      <Button onClick={() => setOpened(true)}>New Project</Button>
      <Modal opened={opened} onClose={() => setOpened(false)} title="Create Project">
        <CreateProjectForm onSuccess={() => setOpened(false)} />
      </Modal>
    </>
  );
}
```

```typescript
// src/components/projects/CreateProjectForm.tsx
'use client';

import { useActionState } from 'react';
import { TextInput, Textarea, Button, Stack, Alert } from '@mantine/core';
import { createProject, type ActionState } from '@/lib/actions/projects';

type CreateProjectFormProps = {
  onSuccess?: () => void;
};

const initialState: ActionState = {
  success: false,
  message: '',
};

export function CreateProjectForm({ onSuccess }: CreateProjectFormProps) {
  const [state, formAction, isPending] = useActionState(createProject, initialState);

  // Call onSuccess when action succeeds (redirect happens server-side)
  // Note: redirect() in server action will handle navigation

  return (
    <form action={formAction}>
      <Stack gap="md">
        {state.message && !state.success && (
          <Alert color="red" title="Error">
            {state.message}
          </Alert>
        )}

        <TextInput
          name="name"
          label="Project Name"
          placeholder="Enter project name"
          required
          error={state.errors?.name?.[0]}
        />

        <Textarea
          name="description"
          label="Description"
          placeholder="Describe your project"
          required
          minRows={3}
          error={state.errors?.description?.[0]}
        />

        <Button type="submit" loading={isPending}>
          Create Project
        </Button>
      </Stack>
    </form>
  );
}
```

```typescript
// src/components/projects/DeleteProjectButton.tsx
'use client';

import { useTransition } from 'react';
import { ActionIcon } from '@mantine/core';
import { IconTrash } from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import { deleteProject } from '@/lib/actions/projects';

type DeleteProjectButtonProps = {
  projectId: string;
};

export function DeleteProjectButton({ projectId }: DeleteProjectButtonProps) {
  const [isPending, startTransition] = useTransition();

  const handleDelete = () => {
    startTransition(async () => {
      const result = await deleteProject(projectId);

      if (result.success) {
        showNotification({
          title: 'Deleted',
          message: result.message,
          color: 'green',
        });
      } else {
        showNotification({
          title: 'Error',
          message: result.message,
          color: 'red',
        });
      }
    });
  };

  return (
    <ActionIcon
      color="red"
      variant="subtle"
      onClick={handleDelete}
      loading={isPending}
      aria-label="Delete project"
    >
      <IconTrash size={16} />
    </ActionIcon>
  );
}
```

### Key Points

- `'use client'` only for interactive components
- `useActionState` for forms with Server Actions
- `useTransition` for non-form mutations with loading state
- Server Action handles database + revalidation + redirect
- Client shows loading state and notifications
- Form uses native `action` attribute (progressive enhancement)

---

## Pattern 6: Dynamic Route with Server Data

Dynamic pages fetch data based on route params.

```typescript
// src/app/projects/[id]/page.tsx
import { notFound } from 'next/navigation';
import { Metadata } from 'next';
import { Stack, Title, Text, Group } from '@mantine/core';
import { getProject } from '@/lib/data/projects';
import { EditProjectButton } from '@/components/projects/EditProjectButton';
import { DeleteProjectButton } from '@/components/projects/DeleteProjectButton';

type PageProps = {
  params: Promise<{ id: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  const project = await getProject(id);

  if (!project) {
    return { title: 'Project Not Found' };
  }

  return {
    title: project.name,
    description: project.description,
  };
}

export default async function ProjectDetailPage({ params }: PageProps) {
  const { id } = await params;
  const project = await getProject(id);

  if (!project) {
    notFound();
  }

  return (
    <Stack gap="lg">
      <Group justify="space-between">
        <Title order={1}>{project.name}</Title>
        <Group gap="xs">
          <EditProjectButton project={project} />
          <DeleteProjectButton projectId={project.id} />
        </Group>
      </Group>
      <Text>{project.description}</Text>
    </Stack>
  );
}
```

### Key Points

- `params` is a Promise in Next.js 15+ (await it)
- `generateMetadata` for dynamic SEO
- `notFound()` renders the not-found page
- Data fetched once, used for metadata and content
- `cache()` deduplicates the `getProject` call

---

## Pattern 7: Layout with Providers

Root layout wrapping the app with providers.

```typescript
// src/app/layout.tsx
import { MantineProvider, ColorSchemeScript } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
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
          {children}
        </MantineProvider>
      </body>
    </html>
  );
}
```

### Key Points

- Root layout is a Server Component
- `ColorSchemeScript` prevents flash of unstyled content
- `MantineProvider` and `Notifications` work in Server Components
- CSS imports at the layout level

---

## Pattern 8: Loading and Error States

Use file-based loading and error handling.

```typescript
// src/app/projects/loading.tsx
import { LoadingOverlay, Center } from '@mantine/core';

export default function ProjectsLoading() {
  return (
    <Center h="50vh">
      <LoadingOverlay visible />
    </Center>
  );
}
```

```typescript
// src/app/projects/error.tsx
'use client';

import { Alert, Button, Stack } from '@mantine/core';

type ErrorProps = {
  error: Error;
  reset: () => void;
};

export default function ProjectsError({ error, reset }: ErrorProps) {
  return (
    <Stack gap="md" align="center">
      <Alert color="red" title="Something went wrong">
        {error.message}
      </Alert>
      <Button onClick={reset}>Try again</Button>
    </Stack>
  );
}
```

```typescript
// src/app/projects/[id]/not-found.tsx
import { Stack, Title, Text, Button } from '@mantine/core';
import Link from 'next/link';

export default function ProjectNotFound() {
  return (
    <Stack gap="md" align="center">
      <Title order={2}>Project Not Found</Title>
      <Text c="dimmed">The project you're looking for doesn't exist.</Text>
      <Button component={Link} href="/projects">
        Back to Projects
      </Button>
    </Stack>
  );
}
```

### Key Points

- `loading.tsx` shows during async data fetching (Server Component)
- `error.tsx` must be a Client Component (needs `reset` function)
- `not-found.tsx` for custom 404 pages
- These are automatic - Next.js uses them based on file location

---

## Quick Reference: When to Use 'use client'

| Scenario | 'use client'? |
|---|---|
| Page fetching data with `await` | **No** (Server Component) |
| Displaying props/data | **No** |
| Mantine layout components (Card, Stack, Text) | **No** |
| Form with Server Action (`action={formAction}`) | **Yes** (needs `useActionState`) |
| Button with `onClick` | **Yes** |
| `useState`, `useEffect`, `useTransition` | **Yes** |
| `useRouter()`, `useSearchParams()` | **Yes** |
| `window`, `document`, `localStorage` | **Yes** |

---

## Quick Reference: Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Page (Server Component)                                        │
│  └─ await getData() ──────────────────────────────────────────┐ │
│                                                                │ │
│  ┌─────────────────────────────────────────────────────────┐  │ │
│  │  lib/data/                                               │  │ │
│  │  └─ Direct DB access or fetch() with caching             │◄─┘ │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  <ChildComponent data={data} />                                  │
│  └─ Props flow down to Server or Client Components               │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Client Component ('use client')                         │    │
│  │  └─ onClick calls Server Action ─────────────────────┐   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                      │           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  lib/actions/ ('use server')                             │    │
│  │  └─ Mutate DB → revalidatePath() → redirect()            │◄───┘
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```
