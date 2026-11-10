# Next.js Page Examples

> **Note:** These examples use plain HTML/JSX for loading and error states.
> Replace with components from your project's configured UI library as specified
> in the style guides.
>
> **Server-first:** pages are async Server Components that `await` data from
> `src/lib/data/` (server-only, `cache()`-wrapped). Client Components only wrap
> interactive parts and receive data as props. Mutations are Server Actions.
>
> **i18n:** next-intl is scaffolded, so pages live under `src/app/[locale]/` and all copy
> comes from `src/messages/<locale>.json` via `getTranslations` / `useTranslations`.
>
> **Params:** `params` and `searchParams` are Promises (Next.js 15+; sync access was
> removed in Next.js 16). Always type them as `Promise<...>` and `await` them.

## Example 1: List Page with Server Data

```typescript
// src/app/[locale]/projects/page.tsx
import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { getProjects } from '@/lib/data/projects';
import { ProjectList } from '@/components/projects/ProjectList';
import { DeleteProjectButton } from '@/components/projects/DeleteProjectButton';
import { Link } from '@/i18n/navigation';

type PageProps = {
  params: Promise<{ locale: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'projects' });
  return { title: t('title'), description: t('description') };
}

export default async function ProjectsPage({ params }: PageProps) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations('projects');
  const projects = await getProjects();

  return (
    <section className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-bold">{t('title')}</h1>
        <Link href="/projects/new" className="btn btn-primary">{t('new')}</Link>
      </div>
      {projects.length === 0 ? (
        <p>{t('empty')}</p>
      ) : (
        // ProjectList is a Server Component; only the delete button is a client island.
        <ProjectList
          projects={projects}
          renderActions={(project) => <DeleteProjectButton projectId={project.id} />}
        />
      )}
    </section>
  );
}
```

```json
// src/messages/en.json (add the same keys to every locale file)
{
  "projects": {
    "title": "Projects",
    "description": "View and manage your projects",
    "new": "New project",
    "empty": "No projects yet."
  }
}
```

---

## Example 2: Dynamic Route with generateMetadata

```typescript
// src/app/[locale]/projects/[id]/page.tsx
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { getProject } from '@/lib/data/projects';
import { ProjectDetail } from '@/components/projects/ProjectDetail';

type PageProps = {
  params: Promise<{ locale: string; id: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale, id } = await params;
  const project = await getProject(id); // cache() dedupes with the page's call

  if (!project) {
    const t = await getTranslations({ locale, namespace: 'projects' });
    return { title: t('notFound') };
  }

  return {
    title: project.name,
    description: project.description,
    openGraph: {
      title: project.name,
      description: project.description,
    },
  };
}

export default async function ProjectDetailPage({ params }: PageProps) {
  const { locale, id } = await params;
  setRequestLocale(locale);

  const project = await getProject(id);
  if (!project) notFound();

  return <ProjectDetail project={project} />;
}
```

---

## Example 3: Authenticated Page with searchParams

```typescript
// src/app/[locale]/dashboard/page.tsx
import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { redirect } from '@/i18n/navigation';
import { auth } from '@/auth';
import { getDashboardData } from '@/lib/data/dashboard';
import { Dashboard } from '@/components/Dashboard';

type PageProps = {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ range?: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'dashboard' });
  return { title: t('title') };
}

export default async function DashboardPage({ params, searchParams }: PageProps) {
  const { locale } = await params;
  const { range = '30d' } = await searchParams;
  setRequestLocale(locale);

  const session = await auth();
  if (!session?.user) {
    redirect({ href: '/login', locale });
  }

  const data = await getDashboardData(session.user.id, range);
  return <Dashboard data={data} user={session.user} />;
}
```

```typescript
// src/lib/data/dashboard.ts
import 'server-only';
import { cache } from 'react';

export const getDashboardData = cache(async (userId: string, range: string) => {
  const res = await fetch(`${process.env.API_URL}/dashboard/${userId}?range=${range}`, {
    next: { revalidate: 300 },
  });
  if (!res.ok) throw new Error('Failed to load dashboard');
  return res.json();
});
```

---

## Example 4: Loading and Error States

```typescript
// src/app/[locale]/projects/loading.tsx
import { getTranslations } from 'next-intl/server';

export default async function ProjectsLoading() {
  const t = await getTranslations('projects');
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
      <div className="spinner" role="status" aria-busy="true" />
      <p className="text-gray-500">{t('loading')}</p>
    </div>
  );
}
```

```typescript
// src/app/[locale]/projects/error.tsx
'use client';

import { useEffect } from 'react';
import { useTranslations } from 'next-intl';

export default function ProjectsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useTranslations('projects');

  useEffect(() => {
    console.error('Projects page error:', error);
  }, [error]);

  return (
    <div className="flex flex-col items-center gap-4 mt-12">
      <div role="alert" className="alert alert-error max-w-lg">
        <h3>{t('loadFailed')}</h3>
      </div>
      <button onClick={reset} className="btn btn-outline">
        {t('retry')}
      </button>
    </div>
  );
}
```

---

## Example 5: Form Pages (Create/Edit)

The page is a Server Component; the form is a client island bound to a Server Action.

```typescript
// src/app/[locale]/projects/new/page.tsx
import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { CreateProjectForm } from '@/components/projects/CreateProjectForm';

type PageProps = {
  params: Promise<{ locale: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'projects' });
  return { title: t('newTitle') };
}

export default async function NewProjectPage({ params }: PageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <CreateProjectForm />;
}
```

```typescript
// src/app/[locale]/projects/[id]/edit/page.tsx
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { getProject } from '@/lib/data/projects';
import { EditProjectForm } from '@/components/projects/EditProjectForm';

type PageProps = {
  params: Promise<{ locale: string; id: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'projects' });
  return { title: t('editTitle') };
}

export default async function EditProjectPage({ params }: PageProps) {
  const { locale, id } = await params;
  setRequestLocale(locale);

  const project = await getProject(id);
  if (!project) notFound();

  // Fetched on the server, passed to the client form as props.
  return <EditProjectForm project={project} />;
}
```

---

## Example 6: Route Group for Authentication

Route groups organize pages without affecting the URL.

```typescript
// src/app/[locale]/(auth)/login/page.tsx
import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { LoginForm } from '@/components/auth/LoginForm';

type PageProps = {
  params: Promise<{ locale: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'auth.login' });
  return { title: t('title') };
}

export default async function LoginPage({ params }: PageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <LoginForm />;
}
```

```typescript
// src/app/[locale]/(auth)/layout.tsx
import { getTranslations } from 'next-intl/server';

export default async function AuthLayout({ children }: { children: React.ReactNode }) {
  const t = await getTranslations('common');
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="w-full max-w-[420px] p-8 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-center mb-6">{t('appName')}</h2>
        {children}
      </div>
    </div>
  );
}
```

---

## Example 7: Not Found Page

```typescript
// src/app/[locale]/not-found.tsx
import { getTranslations } from 'next-intl/server';
import { Link } from '@/i18n/navigation';

export default async function NotFound() {
  const t = await getTranslations('notFound');
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-lg text-gray-500">{t('message')}</p>
      <Link href="/" className="btn btn-outline">
        {t('home')}
      </Link>
    </div>
  );
}
```
