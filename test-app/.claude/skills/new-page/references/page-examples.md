# Next.js Page Examples

> **Note:** These examples use plain HTML/JSX for loading and error states.
> Replace with components from your project's configured UI library as specified
> in the style guides.

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
    next: { revalidate: 300 },
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
export default function ProjectsLoading() {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
      <div className="spinner" aria-label="Loading" />
      <p className="text-gray-500">Loading projects...</p>
    </div>
  );
}
```

```typescript
// src/app/projects/error.tsx
'use client';

import { useEffect } from 'react';

export default function ProjectsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Projects page error:', error);
  }, [error]);

  return (
    <div className="flex flex-col items-center gap-4 mt-12">
      <div role="alert" className="alert alert-error max-w-lg">
        <h3>Failed to load projects</h3>
        <p className="text-sm">{error.message}</p>
      </div>
      <button onClick={reset} className="btn btn-outline">
        Try again
      </button>
    </div>
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
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="w-[420px] p-8 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-center mb-6">My App</h2>
        {children}
      </div>
    </div>
  );
}
```

---

## Example 7: Not Found Page

Custom 404 page.

```typescript
// src/app/not-found.tsx
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-lg text-gray-500">
        The page you are looking for does not exist.
      </p>
      <Link href="/" className="btn btn-outline">
        Go home
      </Link>
    </div>
  );
}
```
