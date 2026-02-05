# Next.js Code Pattern References

## Server Components vs Client Components

### When to Use Server Components (Default)

Server Components are the default in Next.js App Router. Use them for:

- Data fetching from databases or APIs
- Accessing backend resources
- Keeping secrets on the server
- Reducing client-side JavaScript bundle
- Static or SEO-critical content

```typescript
// src/app/projects/page.tsx -- Server Component (default)
import { Metadata } from 'next';
import { ProjectListContainer } from '@/containers/ProjectListContainer';

export const metadata: Metadata = {
  title: 'Projects',
  description: 'View and manage your projects',
};

export default function ProjectsPage() {
  return (
    <main>
      <ProjectListContainer />
    </main>
  );
}
```

### When to Use Client Components ('use client')

Add `'use client'` directive ONLY when the component needs:

1. **React Hooks**: `useState`, `useEffect`, `useContext`, `useReducer`, `useForm`
2. **Event Handlers**: `onClick`, `onChange`, `onSubmit`, `onKeyDown`
3. **Browser APIs**: `window`, `document`, `localStorage`, `navigator`
4. **Third-party client libraries**: Libraries that use hooks or browser APIs

```typescript
'use client';

// This MUST be a client component because it uses useState and onClick
import { useState } from 'react';
import { Button, Text } from '@mantine/core';

export function Counter() {
  const [count, setCount] = useState(0);
  return (
    <>
      <Text>{count}</Text>
      <Button onClick={() => setCount(count + 1)}>Increment</Button>
    </>
  );
}
```

### Common Mistakes

```typescript
// WRONG: This does NOT need 'use client' -- it's purely presentational
'use client'; // REMOVE THIS
import { Card, Text } from '@mantine/core';

type InfoCardProps = { title: string; body: string };

export function InfoCard({ title, body }: InfoCardProps) {
  return (
    <Card>
      <Text fw={500}>{title}</Text>
      <Text>{body}</Text>
    </Card>
  );
}
```

---

## App Router Conventions

### Route Structure

```
src/app/
  layout.tsx          # Root layout (wraps all pages)
  page.tsx            # / route
  loading.tsx         # Loading UI for / route
  error.tsx           # Error UI for / route
  not-found.tsx       # 404 page
  projects/
    page.tsx          # /projects route
    loading.tsx       # Loading UI for /projects
    [id]/
      page.tsx        # /projects/:id route
      loading.tsx     # Loading UI for /projects/:id
    new/
      page.tsx        # /projects/new route
  (auth)/
    login/
      page.tsx        # /login route (grouped, no /auth prefix in URL)
    register/
      page.tsx        # /register route
  api/
    projects/
      route.ts        # API route: /api/projects
      [id]/
        route.ts      # API route: /api/projects/:id
```

### Layout Pattern

```typescript
// src/app/layout.tsx
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';

export const metadata = {
  title: { default: 'My App', template: '%s | My App' },
  description: 'Application description',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <MantineProvider>
          <Notifications position="top-right" />
          {children}
        </MantineProvider>
      </body>
    </html>
  );
}
```

### Loading State

```typescript
// src/app/projects/loading.tsx
import { Center, Loader } from '@mantine/core';

export default function Loading() {
  return (
    <Center h="60vh">
      <Loader size="xl" />
    </Center>
  );
}
```

### Error Boundary

```typescript
// src/app/projects/error.tsx
'use client';

import { Alert, Button, Stack } from '@mantine/core';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <Stack align="center" mt="xl">
      <Alert color="red" title="Something went wrong">
        {error.message}
      </Alert>
      <Button onClick={reset}>Try again</Button>
    </Stack>
  );
}
```

---

## Data Fetching Patterns

### Server-Side Data Fetching (Server Components)

```typescript
// src/app/projects/page.tsx
import { ProjectList } from '@/components/ProjectList';

async function getProjects() {
  const res = await fetch('https://api.example.com/projects', {
    next: { revalidate: 60 }, // Revalidate every 60 seconds
  });
  if (!res.ok) throw new Error('Failed to fetch projects');
  return res.json();
}

export default async function ProjectsPage() {
  const projects = await getProjects();
  return <ProjectList projects={projects} />;
}
```

### Client-Side Data Fetching (Client Components)

Use the IIFE async pattern in containers:

```typescript
'use client';

import { useState, useEffect } from 'react';
import { fetchProjectsApi } from '@/services/projects';

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
        setError(err instanceof Error ? err.message : 'Failed to load');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // render loading, error, or data
}
```

### Dynamic Route Data Fetching

```typescript
// src/app/projects/[id]/page.tsx
import { notFound } from 'next/navigation';

type PageProps = {
  params: { id: string };
};

async function getProject(id: string) {
  const res = await fetch(`https://api.example.com/projects/${id}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Failed to fetch project');
  return res.json();
}

export async function generateMetadata({ params }: PageProps) {
  const project = await getProject(params.id);
  if (!project) return { title: 'Not Found' };
  return { title: project.name, description: project.description };
}

export default async function ProjectPage({ params }: PageProps) {
  const project = await getProject(params.id);
  if (!project) notFound();
  return <ProjectDetail project={project} />;
}
```

---

## Metadata and SEO

### Static Metadata

```typescript
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Projects',
  description: 'Browse and manage your projects',
  openGraph: {
    title: 'Projects',
    description: 'Browse and manage your projects',
    type: 'website',
  },
};
```

### Dynamic Metadata

```typescript
import { Metadata } from 'next';

type PageProps = { params: { id: string } };

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const project = await getProject(params.id);
  return {
    title: project?.name ?? 'Not Found',
    description: project?.description ?? '',
  };
}
```

### Template Metadata (Layout)

```typescript
// src/app/layout.tsx
export const metadata: Metadata = {
  title: {
    default: 'My App',
    template: '%s | My App', // Nested pages: "Projects | My App"
  },
};
```

---

## API Route Handlers

```typescript
// src/app/api/projects/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const page = searchParams.get('page') ?? '1';

  try {
    const projects = await db.project.findMany({
      skip: (parseInt(page) - 1) * 20,
      take: 20,
    });
    return NextResponse.json(projects);
  } catch {
    return NextResponse.json({ error: 'Failed to fetch projects' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validate input
    if (!body.name || body.name.trim().length < 2) {
      return NextResponse.json({ error: 'Name is required' }, { status: 400 });
    }

    const project = await db.project.create({ data: body });
    return NextResponse.json(project, { status: 201 });
  } catch {
    return NextResponse.json({ error: 'Failed to create project' }, { status: 500 });
  }
}
```

```typescript
// src/app/api/projects/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server';

type RouteParams = { params: { id: string } };

export async function GET(request: NextRequest, { params }: RouteParams) {
  const project = await db.project.findUnique({ where: { id: params.id } });
  if (!project) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 });
  }
  return NextResponse.json(project);
}

export async function PATCH(request: NextRequest, { params }: RouteParams) {
  const body = await request.json();
  try {
    const project = await db.project.update({
      where: { id: params.id },
      data: body,
    });
    return NextResponse.json(project);
  } catch {
    return NextResponse.json({ error: 'Failed to update' }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest, { params }: RouteParams) {
  try {
    await db.project.delete({ where: { id: params.id } });
    return new NextResponse(null, { status: 204 });
  } catch {
    return NextResponse.json({ error: 'Failed to delete' }, { status: 500 });
  }
}
```
