# Container Examples

> **Note:** These examples use plain HTML/JSX. Replace with components from your
> project's configured UI library as specified in the style guides.
>
> **Server-first:** a container is a small `'use client'` island. The page (an async
> Server Component) fetches data on the server and passes it in as props. Containers
> handle interaction and call Server Actions; they do not fetch their initial data.

## Example 1: Action Buttons (useTransition + Server Action)

```typescript
// src/components/projects/ProjectRowActions.tsx
'use client';

import { useTransition } from 'react';
import { useTranslations } from 'next-intl';
import { archiveProject, deleteProject } from '@/lib/actions/projects';

type ProjectRowActionsProps = {
  projectId: string;
  status: 'active' | 'archived' | 'draft';
};

/** Archive/delete buttons for one project row; the list itself is a Server Component. */
export function ProjectRowActions({ projectId, status }: ProjectRowActionsProps) {
  const t = useTranslations('projects.actions');
  const [isPending, startTransition] = useTransition();

  return (
    <div className="flex gap-2">
      {status !== 'archived' && (
        <button
          disabled={isPending}
          onClick={() => startTransition(() => archiveProject(projectId))}
        >
          {t('archive')}
        </button>
      )}
      <button
        disabled={isPending}
        onClick={() => startTransition(() => deleteProject(projectId))}
      >
        {isPending ? t('deleting') : t('delete')}
      </button>
    </div>
  );
}
```

```typescript
// src/app/[locale]/projects/page.tsx (excerpt) — data fetched on the server
const projects = await getProjects();
return (
  <ul>
    {projects.map((p) => (
      <li key={p.id}>
        {p.name}
        <ProjectRowActions projectId={p.id} status={p.status} />
      </li>
    ))}
  </ul>
);
```

---

## Example 2: Create Form (useActionState)

```typescript
// src/components/projects/CreateProjectForm.tsx
'use client';

import { useActionState } from 'react';
import { useTranslations } from 'next-intl';
import { createProject, type ProjectFormState } from '@/lib/actions/projects';

const initialState: ProjectFormState = { status: 'idle' };

export function CreateProjectForm() {
  const t = useTranslations('projects.form');
  // createProject(prevState, formData) — the signature useActionState expects
  const [state, formAction, isPending] = useActionState(createProject, initialState);

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label htmlFor="name">{t('name')}</label>
        <input id="name" name="name" required />
        {state.status === 'error' && state.fieldErrors?.name && (
          <p className="text-red-600">{state.fieldErrors.name[0]}</p>
        )}
      </div>
      <div>
        <label htmlFor="description">{t('description')}</label>
        <textarea id="description" name="description" />
      </div>
      {state.status === 'error' && !state.fieldErrors && (
        <p role="alert" className="text-red-600">{state.error}</p>
      )}
      <button type="submit" disabled={isPending}>
        {isPending ? t('submitting') : t('create')}
      </button>
    </form>
  );
}
```

---

## Example 3: Edit Form (pre-filled from server data)

The page fetched the project; the form only receives it.

```typescript
// src/components/projects/EditProjectForm.tsx
'use client';

import { useActionState } from 'react';
import { useTranslations } from 'next-intl';
import { updateProject, type ProjectFormState } from '@/lib/actions/projects';

type EditProjectFormProps = {
  project: { id: string; name: string; description: string };
};

const initialState: ProjectFormState = { status: 'idle' };

export function EditProjectForm({ project }: EditProjectFormProps) {
  const t = useTranslations('projects.form');
  // Bind the id; the action still re-checks that the user owns it.
  const [state, formAction, isPending] = useActionState(
    updateProject.bind(null, project.id),
    initialState
  );

  return (
    <form action={formAction} className="space-y-4">
      <label htmlFor="name">{t('name')}</label>
      <input id="name" name="name" defaultValue={project.name} required />
      {state.status === 'error' && state.fieldErrors?.name && (
        <p className="text-red-600">{state.fieldErrors.name[0]}</p>
      )}

      <label htmlFor="description">{t('description')}</label>
      <textarea id="description" name="description" defaultValue={project.description} />

      <button type="submit" disabled={isPending}>
        {isPending ? t('saving') : t('save')}
      </button>
    </form>
  );
}
```

```typescript
// src/lib/actions/projects.ts (excerpt)
'use server';

export async function updateProject(
  projectId: string,
  _prevState: ProjectFormState,
  formData: FormData
): Promise<ProjectFormState> {
  const user = await requireUser();                       // authenticate
  const parsed = ProjectSchema.safeParse(Object.fromEntries(formData)); // validate
  if (!parsed.success) {
    return { status: 'error', error: 'Validation failed', fieldErrors: z.flattenError(parsed.error).fieldErrors };
  }
  const { count } = await db.project.updateMany({          // authorize (owner-scoped)
    where: { id: projectId, ownerId: user.id },
    data: parsed.data,
  });
  if (count === 0) return { status: 'error', error: 'Not found' };
  revalidatePath('/[locale]/projects', 'layout');
  redirect(`/projects/${projectId}`);
}
```

---

## Example 4: Filters and Pagination via the URL

Filters write to `searchParams`; the server page reads them and re-fetches.
No client fetching needed.

```typescript
// src/components/projects/ProjectFilters.tsx
'use client';

import { useTransition } from 'react';
import { useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { usePathname, useRouter } from '@/i18n/navigation';

export function ProjectFilters() {
  const t = useTranslations('projects.filters');
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const setParam = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams);
    if (value) params.set(key, value);
    else params.delete(key);
    params.delete('page'); // reset pagination on filter change
    startTransition(() => router.replace(`${pathname}?${params.toString()}`));
  };

  return (
    <div className="flex gap-3" aria-busy={isPending}>
      <input
        type="search"
        placeholder={t('search')}
        defaultValue={searchParams.get('q') ?? ''}
        onChange={(e) => setParam('q', e.target.value)}
      />
      <select
        defaultValue={searchParams.get('status') ?? ''}
        onChange={(e) => setParam('status', e.target.value)}
      >
        <option value="">{t('allStatuses')}</option>
        <option value="active">{t('active')}</option>
        <option value="archived">{t('archived')}</option>
      </select>
    </div>
  );
}
```

```typescript
// src/app/[locale]/projects/page.tsx (excerpt)
type PageProps = {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ q?: string; status?: string; page?: string }>;
};

export default async function ProjectsPage({ params, searchParams }: PageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const { q, status, page = '1' } = await searchParams;
  const result = await getProjects({ q, status, page: Number(page) || 1 });
  return (
    <>
      <ProjectFilters />
      <ProjectList projects={result.data} />
    </>
  );
}
```

---

## Example 5: Genuinely Client-Driven Data (polling)

Only when data must update without navigation (live status, notifications, infinite
scroll). The server still renders the first state and passes it as `initialData`.
Use TanStack Query if the project has it.

```typescript
// src/components/deployments/DeploymentStatus.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';

type Deployment = { id: string; status: 'queued' | 'running' | 'done' | 'failed' };

export function DeploymentStatus({ initialData }: { initialData: Deployment }) {
  const t = useTranslations('deployments');
  const { data } = useQuery({
    queryKey: ['deployment', initialData.id],
    // A Route Handler that authenticates the caller like a Server Action does.
    queryFn: async (): Promise<Deployment> => {
      const res = await fetch(`/api/deployments/${initialData.id}`);
      if (!res.ok) throw new Error(String(res.status));
      return res.json();
    },
    initialData,
    refetchInterval: (query) =>
      query.state.data?.status === 'running' || query.state.data?.status === 'queued' ? 3000 : false,
  });

  return <span>{t(`status.${data.status}`)}</span>;
}
```

---

## Container Test Pattern

Containers are tested with props in and Server Actions mocked — no fetch mocks.

```typescript
// src/components/projects/ProjectRowActions.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NextIntlClientProvider } from 'next-intl';
import messages from '@/messages/en.json';
import { ProjectRowActions } from './ProjectRowActions';
import { deleteProject } from '@/lib/actions/projects';

jest.mock('@/lib/actions/projects', () => ({
  deleteProject: jest.fn().mockResolvedValue(undefined),
  archiveProject: jest.fn().mockResolvedValue(undefined),
}));

const renderWithIntl = (ui: React.ReactElement) =>
  render(
    <NextIntlClientProvider locale="en" messages={messages}>
      {ui}
    </NextIntlClientProvider>
  );

describe('ProjectRowActions', () => {
  beforeEach(() => jest.clearAllMocks());

  it('calls the deleteProject action with the project id', async () => {
    renderWithIntl(<ProjectRowActions projectId="p1" status="active" />);

    fireEvent.click(screen.getByRole('button', { name: /delete/i }));

    await waitFor(() => expect(deleteProject).toHaveBeenCalledWith('p1'));
  });

  it('hides archive for archived projects', () => {
    renderWithIntl(<ProjectRowActions projectId="p1" status="archived" />);

    expect(screen.queryByRole('button', { name: /archive/i })).not.toBeInTheDocument();
  });
});
```
