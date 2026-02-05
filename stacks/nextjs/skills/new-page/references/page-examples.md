# Next.js Page Examples

## Example 1: Static Page with Metadata

A simple page that delegates to a container component.

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

---

## Example 2: Dynamic Route with generateMetadata

A page that uses URL params and generates dynamic metadata.

```typescript
// src/app/projects/[id]/page.tsx
import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { ProjectDetailContainer } from '@/containers/ProjectDetailContainer';

type PageProps = {
  params: { id: string };
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  // In a server component, you can fetch data directly
  const res = await fetch(`${process.env.API_URL}/projects/${params.id}`, {
    next: { revalidate: 60 },
  });

  if (!res.ok) {
    return { title: 'Project Not Found' };
  }

  const project = await res.json();
  return {
    title: project.name,
    description: project.description,
    openGraph: {
      title: project.name,
      description: project.description,
    },
  };
}

export default function ProjectDetailPage({ params }: PageProps) {
  return <ProjectDetailContainer id={params.id} />;
}
```

---

## Example 3: Server-Side Data Fetching Page

A page that fetches data on the server and passes it to a presentational component.

```typescript
// src/app/dashboard/page.tsx
import { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { getServerSession } from 'next-auth';
import { Dashboard } from '@/components/Dashboard';

export const metadata: Metadata = {
  title: 'Dashboard',
  description: 'Your project dashboard',
};

async function getDashboardData(userId: string) {
  const res = await fetch(`${process.env.API_URL}/dashboard/${userId}`, {
    next: { revalidate: 300 }, // Cache for 5 minutes
  });
  if (!res.ok) throw new Error('Failed to load dashboard');
  return res.json();
}

export default async function DashboardPage() {
  const session = await getServerSession();
  if (!session?.user) {
    redirect('/login');
  }

  const data = await getDashboardData(session.user.id);
  return <Dashboard data={data} user={session.user} />;
}
```

---

## Example 4: Page with Loading and Error States

Complete set of files for a route with loading and error handling.

```typescript
// src/app/projects/page.tsx
import { Metadata } from 'next';
import { ProjectListContainer } from '@/containers/ProjectListContainer';

export const metadata: Metadata = {
  title: 'Projects',
  description: 'Browse all projects',
};

export default function ProjectsPage() {
  return <ProjectListContainer />;
}
```

```typescript
// src/app/projects/loading.tsx
import { Center, Loader, Stack, Text } from '@mantine/core';

export default function ProjectsLoading() {
  return (
    <Center h="60vh">
      <Stack align="center" gap="md">
        <Loader size="xl" />
        <Text c="dimmed">Loading projects...</Text>
      </Stack>
    </Center>
  );
}
```

```typescript
// src/app/projects/error.tsx
'use client';

import { useEffect } from 'react';
import { Alert, Button, Stack, Text } from '@mantine/core';
import { IconAlertTriangle } from '@tabler/icons-react';

export default function ProjectsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Projects page error:', error);
  }, [error]);

  return (
    <Stack align="center" mt="xl" gap="md">
      <IconAlertTriangle size={48} color="var(--mantine-color-red-6)" />
      <Alert color="red" title="Failed to load projects" maw={500}>
        <Text size="sm">{error.message}</Text>
      </Alert>
      <Button onClick={reset} variant="outline">
        Try again
      </Button>
    </Stack>
  );
}
```

---

## Example 5: Form Page (Create/Edit)

A page for creating or editing a resource.

```typescript
// src/app/projects/new/page.tsx
import { Metadata } from 'next';
import { CreateProjectContainer } from '@/containers/CreateProjectContainer';

export const metadata: Metadata = {
  title: 'New Project',
  description: 'Create a new project',
};

export default function NewProjectPage() {
  return <CreateProjectContainer />;
}
```

```typescript
// src/app/projects/[id]/edit/page.tsx
import { Metadata } from 'next';
import { EditProjectContainer } from '@/containers/EditProjectContainer';

type PageProps = {
  params: { id: string };
};

export const metadata: Metadata = {
  title: 'Edit Project',
};

export default function EditProjectPage({ params }: PageProps) {
  return <EditProjectContainer id={params.id} />;
}
```

---

## Example 6: Route Group for Authentication

Using route groups to organize auth pages without affecting the URL.

```typescript
// src/app/(auth)/login/page.tsx
import { Metadata } from 'next';
import { LoginContainer } from '@/containers/LoginContainer';

export const metadata: Metadata = {
  title: 'Sign In',
  description: 'Sign in to your account',
};

export default function LoginPage() {
  return <LoginContainer />;
}
```

```typescript
// src/app/(auth)/layout.tsx
import { Center, Paper, Stack, Title } from '@mantine/core';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <Center h="100vh" bg="gray.0">
      <Paper shadow="md" p="xl" radius="md" w={420}>
        <Stack>
          <Title order={2} ta="center">
            My App
          </Title>
          {children}
        </Stack>
      </Paper>
    </Center>
  );
}
```

---

## Example 7: Not Found Page

Custom 404 page.

```typescript
// src/app/not-found.tsx
import { Center, Stack, Title, Text, Button } from '@mantine/core';
import Link from 'next/link';

export default function NotFound() {
  return (
    <Center h="60vh">
      <Stack align="center" gap="md">
        <Title order={1}>404</Title>
        <Text c="dimmed" size="lg">
          The page you are looking for does not exist.
        </Text>
        <Button component={Link} href="/" variant="outline">
          Go home
        </Button>
      </Stack>
    </Center>
  );
}
```
