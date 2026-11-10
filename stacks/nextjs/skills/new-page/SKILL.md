---
name: new-page
description: Generate a new Next.js App Router page (async Server Component) with metadata, translations, loading, and error states
---

# /new-page

## What This Does

Creates a new Next.js App Router page as an **async Server Component** that fetches
its data on the server, with metadata, translated copy, a loading state and an error
boundary. Interactive parts are small Client Components ("containers") that receive
data as props.

Data flow (server-first):

```
page.tsx (async Server Component)
  -> await getX() from src/lib/data/   (server-only, cache()-wrapped)
  -> renders Server Components with the data
  -> renders 'use client' islands with the data as props (only for interactivity)
  -> mutations go through Server Actions in src/lib/actions/
```

## Usage

```
/new-page /projects
/new-page /projects/[id]
/new-page /projects/new
/new-page /settings/profile
/new-page /(auth)/login
```

## How It Works

### 1. Parse the Route

next-intl is scaffolded (`src/i18n/`, `src/proxy.ts`), so every page lives under the
`[locale]` segment:

| Input | Directory |
|---|---|
| `/projects` | `src/app/[locale]/projects/` |
| `/projects/[id]` | `src/app/[locale]/projects/[id]/` |
| `/projects/new` | `src/app/[locale]/projects/new/` |
| `/(auth)/login` | `src/app/[locale]/(auth)/login/` |

If the project has no `src/app/[locale]/` directory (i18n was removed), drop the
`[locale]` segment and the translation calls below.

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` and `patterns/i18n.md` for conventions
- `skills/new-page/references/page-examples.md` for examples
- The project's UI library style guide (in `styles/`) for loading/error components
- Existing pages in `src/app/[locale]/` and data functions in `src/lib/data/`

### 3. Generate Files

#### `page.tsx` -- The page component

```typescript
import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { get<Name>s } from '@/lib/data/<name>s';
import { <Name>List } from '@/components/<name>s/<Name>List';

type PageProps = {
  params: Promise<{ locale: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: '<name>s' });
  return { title: t('title'), description: t('description') };
}

export default async function <Name>sPage({ params }: PageProps) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations('<name>s');
  const items = await get<Name>s();

  return (
    <section>
      <h1>{t('title')}</h1>
      <<Name>List items={items} />
    </section>
  );
}
```

For dynamic routes (`[id]`), `params` (and `searchParams`) are **Promises** (Next.js 15+;
synchronous access was removed in Next.js 16) — always `await` them:

```typescript
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { get<Name> } from '@/lib/data/<name>s';
import { <Name>Detail } from '@/components/<name>s/<Name>Detail';

type PageProps = {
  params: Promise<{ locale: string; id: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale, id } = await params;
  const item = await get<Name>(id); // cache() dedupes this with the page's call
  const t = await getTranslations({ locale, namespace: '<name>s' });
  return { title: item?.name ?? t('notFound') };
}

export default async function <Name>Page({ params, searchParams }: PageProps) {
  const { locale, id } = await params;
  const { tab } = await searchParams;
  setRequestLocale(locale);

  const item = await get<Name>(id);
  if (!item) notFound();

  return <<Name>Detail item={item} activeTab={typeof tab === 'string' ? tab : undefined} />;
}
```

Add the new keys (`title`, `description`, ...) to **every** file in `src/messages/`
(at least the default locale; mirror the keys in the others). Never hardcode
user-facing copy in the page.

#### `loading.tsx` -- Loading state (Suspense fallback while the page awaits data)

Use the project's UI library loading components (see style guides).

```typescript
export default function Loading() {
  return (
    <div className="flex items-center justify-center h-[60vh]">
      {/* Use UI library's Loader/Spinner component */}
      <div className="spinner" role="status" aria-busy="true" />
    </div>
  );
}
```

#### `error.tsx` -- Error boundary

Error boundaries must be Client Components. Use the project's UI library
error/alert components (see style guides).

```typescript
'use client';

import { useTranslations } from 'next-intl';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useTranslations('common');

  return (
    <div className="flex flex-col items-center gap-4 mt-8">
      <div role="alert" className="alert alert-error">
        <h3>{t('error')}</h3>
      </div>
      <button onClick={reset} className="btn">{t('retry')}</button>
    </div>
  );
}
```

### 4. Interactive Islands (Optional)

If part of the page needs interactivity (delete button, filters, a form), run
`/new-container <Name>` to create a small `'use client'` component that **receives
data as props** and calls Server Actions. Do not move the page's data fetching into it.

### 5. Verify

Run `npx tsc --noEmit` to verify the page compiles without errors.

## Rules

- Pages are async Server Components (no `'use client'`) that `await` data from `src/lib/data/`
- No `useEffect`/client fetching for the page's own data
- `params` and `searchParams` are typed as `Promise<...>` and awaited
- Pages live under `src/app/[locale]/` and call `setRequestLocale(locale)`
- All copy comes from `getTranslations` (server) / `useTranslations` (client); no hardcoded strings
- Pages define metadata (`generateMetadata` when it depends on params or translations)
- Every page directory includes `loading.tsx` and `error.tsx`
- Use `notFound()` from `next/navigation` for 404 cases in dynamic routes
- Pages that show private data check the session on the server (redirect if signed out)
- Use the project's UI library for loading/error components (see style guides)

## Output

```
Created:
  src/app/[locale]/<route>/page.tsx      -- Async Server Component with metadata
  src/app/[locale]/<route>/loading.tsx   -- Loading state
  src/app/[locale]/<route>/error.tsx     -- Error boundary
  src/messages/*.json                    -- New translation keys

Suggested:
  /new-container <Name>  -- If the page needs an interactive island

Verified:
  npx tsc --noEmit  -- PASS
```
