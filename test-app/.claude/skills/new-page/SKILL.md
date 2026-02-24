---
name: new-page
description: Generate a new Next.js App Router page with metadata, loading, and error states
---

# /new-page

## What This Does

Creates a new Next.js App Router page with proper metadata, loading state,
error boundary, and container delegation. Follows the Page -> Container ->
Component pattern.

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

Convert the route path to the App Router directory structure:

| Input | Directory |
|---|---|
| `/projects` | `src/app/projects/` |
| `/projects/[id]` | `src/app/projects/[id]/` |
| `/projects/new` | `src/app/projects/new/` |
| `/(auth)/login` | `src/app/(auth)/login/` |

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` for conventions
- `skills/new-page/references/page-examples.md` for examples
- The project's UI library style guide (in `styles/`) for loading/error components
- Existing pages in `src/app/` for project-specific patterns

### 3. Generate Files

Create the following files in the route directory:

#### `page.tsx` -- The page component

```typescript
import { Metadata } from 'next';
import { <Name>Container } from '@/containers/<Name>Container';

export const metadata: Metadata = {
  title: '<Page Title>',
  description: '<Page description for SEO>',
};

export default function <Name>Page() {
  return <<Name>Container />;
}
```

For dynamic routes (`[id]`):

```typescript
import { Metadata } from 'next';
import { <Name>Container } from '@/containers/<Name>Container';

type PageProps = {
  params: { id: string };
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  return {
    title: `<Resource> ${params.id}`,
  };
}

export default function <Name>Page({ params }: PageProps) {
  return <<Name>Container id={params.id} />;
}
```

#### `loading.tsx` -- Loading state

Use the project's UI library loading components (see style guides).

```typescript
export default function Loading() {
  return (
    <div className="flex items-center justify-center h-[60vh]">
      {/* Use UI library's Loader/Spinner component */}
      <div className="spinner" aria-label="Loading" />
    </div>
  );
}
```

#### `error.tsx` -- Error boundary

Use the project's UI library error/alert components (see style guides).

```typescript
'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-4 mt-8">
      <div role="alert" className="alert alert-error">
        <h3>Something went wrong</h3>
        <p>{error.message}</p>
      </div>
      <button onClick={reset} className="btn">Try again</button>
    </div>
  );
}
```

### 4. Generate Container (Optional)

If no matching container exists in `src/containers/`, suggest running
`/new-container <Name>` to create the data-fetching container.

### 5. Verify

Run `npx tsc --noEmit` to verify the page compiles without errors.

## Rules

- Pages are Server Components by default (no `'use client'`)
- Pages delegate to containers for data fetching
- Pages define metadata for SEO
- Dynamic routes include `generateMetadata`
- Every page directory includes `loading.tsx` and `error.tsx`
- Use `notFound()` from `next/navigation` for 404 cases in dynamic routes
- Use the project's UI library for loading/error components (see style guides)

## Output

```
Created:
  src/app/<route>/page.tsx      -- Page component with metadata
  src/app/<route>/loading.tsx   -- Loading state
  src/app/<route>/error.tsx     -- Error boundary

Suggested:
  /new-container <Name>  -- If container does not exist yet

Verified:
  npx tsc --noEmit  -- PASS
```
