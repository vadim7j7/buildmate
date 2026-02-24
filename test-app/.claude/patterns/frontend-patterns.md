# React / Next.js Code Patterns

Reference patterns for code generation following Next.js App Router conventions.
**Server Components are the default.** Only use Client Components when necessary.

> **Note:** These examples use plain HTML/JSX. Replace with components from your
> project's configured UI library as specified in the style guides.

---

## Pattern 1: Page with Server-Side Data Fetching (DEFAULT)

The primary pattern. Pages are async Server Components that fetch data directly.

```typescript
// src/app/projects/page.tsx
import { Metadata } from 'next';
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
    <div className="space-y-6">
      <h1>Projects</h1>
      <CreateProjectButton />
      <ProjectList projects={projects} />
    </div>
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
import { ProjectCard } from './ProjectCard';
import type { Project } from '@/lib/data/projects';

type ProjectListProps = {
  projects: Project[];
};

export function ProjectList({ projects }: ProjectListProps) {
  if (projects.length === 0) {
    return <p className="text-muted">No projects yet. Create your first project!</p>;
  }

  return (
    <div className="space-y-4">
      {projects.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
```

```typescript
// src/components/projects/ProjectCard.tsx
import Link from 'next/link';
import { DeleteProjectButton } from './DeleteProjectButton';
import type { Project } from '@/lib/data/projects';

type ProjectCardProps = {
  project: Project;
};

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link href={`/projects/${project.id}`} className="block p-4 rounded-lg border shadow-sm">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-medium">{project.name}</h3>
          <p className="text-sm text-muted mt-1">
            {project.description}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`badge ${project.status === 'active' ? 'badge-success' : 'badge-default'}`}>
            {project.status}
          </span>
          <DeleteProjectButton projectId={project.id} />
        </div>
      </div>
    </Link>
  );
}
```

### Key Points

- No `'use client'` directive
- Pure presentational components receiving props
- Can use Next.js `Link` for navigation
- Interactive children (buttons) are separate Client Components
- Use your UI library's components in place of plain HTML elements

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
import { CreateProjectForm } from './CreateProjectForm';

export function CreateProjectButton() {
  const [opened, setOpened] = useState(false);

  return (
    <>
      <button onClick={() => setOpened(true)} className="btn btn-primary">
        New Project
      </button>
      {opened && (
        <dialog open className="modal">
          <div className="modal-content">
            <h2>Create Project</h2>
            <CreateProjectForm onSuccess={() => setOpened(false)} />
            <button onClick={() => setOpened(false)}>Close</button>
          </div>
        </dialog>
      )}
    </>
  );
}
```

```typescript
// src/components/projects/CreateProjectForm.tsx
'use client';

import { useActionState } from 'react';
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

  return (
    <form action={formAction}>
      <div className="space-y-4">
        {state.message && !state.success && (
          <div role="alert" className="alert alert-error">
            {state.message}
          </div>
        )}

        <div>
          <label htmlFor="name">Project Name</label>
          <input
            id="name"
            name="name"
            placeholder="Enter project name"
            required
          />
          {state.errors?.name?.[0] && (
            <p className="text-error text-sm">{state.errors.name[0]}</p>
          )}
        </div>

        <div>
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            placeholder="Describe your project"
            required
            rows={3}
          />
          {state.errors?.description?.[0] && (
            <p className="text-error text-sm">{state.errors.description[0]}</p>
          )}
        </div>

        <button type="submit" disabled={isPending} className="btn btn-primary">
          {isPending ? 'Creating...' : 'Create Project'}
        </button>
      </div>
    </form>
  );
}
```

```typescript
// src/components/projects/DeleteProjectButton.tsx
'use client';

import { useTransition } from 'react';
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
        // Show success feedback using your UI library's notification system
      } else {
        // Show error feedback using your UI library's notification system
      }
    });
  };

  return (
    <button
      onClick={handleDelete}
      disabled={isPending}
      aria-label="Delete project"
      className="btn btn-icon btn-danger"
    >
      {isPending ? '...' : '✕'}
    </button>
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
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1>{project.name}</h1>
        <div className="flex gap-2">
          <EditProjectButton project={project} />
          <DeleteProjectButton projectId={project.id} />
        </div>
      </div>
      <p>{project.description}</p>
    </div>
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
import '@/styles/globals.css';

export const metadata = {
  title: { default: 'My App', template: '%s | My App' },
  description: 'Application description',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {/* Wrap with your UI library's provider if needed */}
        {children}
      </body>
    </html>
  );
}
```

### Key Points

- Root layout is a Server Component
- Wrap with your UI library's provider (e.g., MantineProvider, ThemeProvider)
- CSS imports at the layout level
- See your UI library's style guide for provider setup details

---

## Pattern 8: Loading and Error States

Use file-based loading and error handling.

```typescript
// src/app/projects/loading.tsx
export default function ProjectsLoading() {
  return (
    <div className="flex items-center justify-center h-[50vh]">
      <div className="spinner" aria-label="Loading" />
    </div>
  );
}
```

```typescript
// src/app/projects/error.tsx
'use client';

type ErrorProps = {
  error: Error;
  reset: () => void;
};

export default function ProjectsError({ error, reset }: ErrorProps) {
  return (
    <div className="flex flex-col items-center gap-4">
      <div role="alert" className="alert alert-error">
        <h3>Something went wrong</h3>
        <p>{error.message}</p>
      </div>
      <button onClick={reset} className="btn">Try again</button>
    </div>
  );
}
```

```typescript
// src/app/projects/[id]/not-found.tsx
import Link from 'next/link';

export default function ProjectNotFound() {
  return (
    <div className="flex flex-col items-center gap-4">
      <h2>Project Not Found</h2>
      <p className="text-muted">The project you're looking for doesn't exist.</p>
      <Link href="/projects" className="btn">
        Back to Projects
      </Link>
    </div>
  );
}
```

### Key Points

- `loading.tsx` shows during async data fetching (Server Component)
- `error.tsx` must be a Client Component (needs `reset` function)
- `not-found.tsx` for custom 404 pages
- These are automatic - Next.js uses them based on file location
- Replace plain HTML with your UI library's components

---

## Quick Reference: When to Use 'use client'

| Scenario | 'use client'? |
|---|---|
| Page fetching data with `await` | **No** (Server Component) |
| Displaying props/data | **No** |
| UI library layout components (cards, stacks, text) | **No** (usually) |
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
