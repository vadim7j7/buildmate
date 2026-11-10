---
name: new-server-action
description: Generate a Next.js Server Action with auth checks and Zod validation
---

# /new-server-action

## What This Does

Creates a Next.js Server Action with authentication, authorization, Zod input
validation, error handling, and TypeScript types. Server Actions are the way this
app performs mutations from React components.

**Every Server Action is a public POST endpoint.** Anyone can call it with any
arguments, whether or not your UI shows the button. Hiding UI, checking in the
page, or redirecting in `proxy.ts` does **not** protect the action. Each action
must itself:

1. **Authenticate** — get the session; return/throw if signed out.
2. **Authorize** — check the user may touch *this* resource (ownership, role, tenant).
3. **Validate** — parse every argument (including `FormData` and IDs) with Zod.

## Usage

```
/new-server-action createProject      # Creates createProject action
/new-server-action updateProfile      # Creates updateProfile action
/new-server-action submitContact      # Creates submitContact action (public: no auth, but rate-limit)
/new-server-action deletePost         # Creates deletePost action
```

## How It Works

### 1. Determine Action Purpose

Based on the action name, infer:
- Who may call it (signed-in user? owner? admin? truly public?)
- What data the action accepts and what validation is needed
- What side effects occur (database, backend API, email, etc.)
- What to revalidate and where to redirect afterwards

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` and `patterns/auth.md` for conventions
- `skills/new-server-action/references/server-action-examples.md` for examples
- Existing actions in `src/lib/actions/` and the session helper in `src/lib/auth` / `src/auth.ts`

### 3. Generate Files

#### Action: `src/lib/actions/<resource>.ts`

Two call styles:

- **Form actions** (used with `<form action>` / `useActionState`) take
  `(prevState: State, formData: FormData)`.
- **Programmatic actions** (called from an event handler / `startTransition`) take
  typed arguments — but those arguments are still untrusted and are validated.

```typescript
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { requireUser } from '@/lib/auth'; // returns the session user or throws/redirects
import { db } from '@/lib/db';

const <ActionName>Schema = z.object({
  // Input validation schema
});

export type <ActionName>State =
  | { status: 'idle' }
  | { status: 'success' }
  | { status: 'error'; error: string; fieldErrors?: Record<string, string[] | undefined> };

export async function <actionName>(
  _prevState: <ActionName>State,
  formData: FormData
): Promise<<ActionName>State> {
  // 1. Authenticate
  const user = await requireUser();

  // 2. Validate (never trust client input)
  const parsed = <ActionName>Schema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) {
    return {
      status: 'error',
      error: 'Validation failed',
      fieldErrors: z.flattenError(parsed.error).fieldErrors,
    };
  }

  // 3. Authorize against the resource being changed
  //    e.g. const item = await db.item.findFirst({ where: { id, ownerId: user.id } });
  //    if (!item) return { status: 'error', error: 'Not found' };

  try {
    await doSomething(parsed.data, user.id);
  } catch (error) {
    console.error('<actionName> failed:', error);
    return { status: 'error', error: 'Operation failed' }; // no internal details
  }

  revalidatePath('/[locale]/<path>', 'page');
  return { status: 'success' };
}
```

#### Test: `src/lib/actions/<resource>.test.ts`

Test at least: signed-out caller is rejected, a user who does not own the resource
is rejected, invalid input returns field errors, the happy path mutates and revalidates.

### 4. Verify

Run type checking:
```bash
npx tsc --noEmit
```

## Rules

- Always use the `'use server'` directive at the top of the file
- **Authenticate and authorize inside every action** — never rely on the page,
  the UI, or `proxy.ts` having checked
- Scope every query by the user (`where: { id, ownerId: user.id }`) so IDs from the
  client cannot reach other users' data
- Validate all inputs with Zod (`safeParse`), including IDs and `FormData`
- Report field errors with `z.flattenError(error).fieldErrors` (Zod 4; `error.flatten()` is deprecated)
- Form actions take `(prevState, formData)` so they work with `useActionState`
- Return a typed result for expected failures; never expose internal error details
- Use `revalidatePath` or `revalidateTag` after mutations
- Call `redirect()` **outside** `try/catch` (it throws to navigate)
- Truly public actions (contact form, sign-up) skip auth but must validate and be rate-limited
- Do not return secrets or whole DB rows to the client — return only what the UI needs

## Generated Files

```
src/lib/actions/<resource>.ts
src/lib/actions/<resource>.test.ts
```

## Example Output

For `/new-server-action createProject`:

**Action:** `src/lib/actions/projects.ts`
```typescript
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { requireUser } from '@/lib/auth';
import { db } from '@/lib/db';

const CreateProjectSchema = z.object({
  name: z.string().trim().min(2).max(100),
  description: z.string().trim().max(1000).default(''),
});

export type CreateProjectState =
  | { status: 'idle' }
  | { status: 'error'; error: string; fieldErrors?: Record<string, string[] | undefined> };

export async function createProject(
  _prevState: CreateProjectState,
  formData: FormData
): Promise<CreateProjectState> {
  const user = await requireUser();

  const parsed = CreateProjectSchema.safeParse({
    name: formData.get('name'),
    description: formData.get('description') ?? undefined,
  });
  if (!parsed.success) {
    return {
      status: 'error',
      error: 'Validation failed',
      fieldErrors: z.flattenError(parsed.error).fieldErrors,
    };
  }

  try {
    await db.project.create({ data: { ...parsed.data, ownerId: user.id } });
  } catch (error) {
    console.error('createProject failed:', error);
    return { status: 'error', error: 'Could not create the project' };
  }

  revalidatePath('/[locale]/projects', 'page');
  redirect('/projects');
}

const ProjectIdSchema = z.string().uuid();

export async function deleteProject(projectId: string): Promise<void> {
  const user = await requireUser();
  const id = ProjectIdSchema.parse(projectId);

  // Scoped by owner: a forged ID for someone else's project deletes nothing.
  const { count } = await db.project.deleteMany({ where: { id, ownerId: user.id } });
  if (count === 0) throw new Error('Not found');

  revalidatePath('/[locale]/projects', 'page');
}
```

**Component Usage:**
```typescript
'use client';

import { useActionState } from 'react';
import { useTranslations } from 'next-intl';
import { createProject, type CreateProjectState } from '@/lib/actions/projects';

const initialState: CreateProjectState = { status: 'idle' };

export function CreateProjectForm() {
  const t = useTranslations('projects.form');
  const [state, formAction, isPending] = useActionState(createProject, initialState);

  return (
    <form action={formAction}>
      <label htmlFor="name">{t('name')}</label>
      <input id="name" name="name" required />
      {state.status === 'error' && state.fieldErrors?.name && (
        <span className="error">{state.fieldErrors.name[0]}</span>
      )}

      <label htmlFor="description">{t('description')}</label>
      <textarea id="description" name="description" />

      <button type="submit" disabled={isPending}>
        {isPending ? t('submitting') : t('submit')}
      </button>

      {state.status === 'error' && !state.fieldErrors && (
        <div role="alert" className="error">{state.error}</div>
      )}
    </form>
  );
}
```
