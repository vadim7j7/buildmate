---
name: new-layout
description: Generate a Next.js layout with metadata, loading, and error states
---

# /new-layout

## What This Does

Creates a Next.js App Router layout with:
- TypeScript layout component
- Metadata configuration
- Loading UI (loading.tsx)
- Error boundary (error.tsx)
- Not found page (not-found.tsx) if appropriate

## Usage

```
/new-layout dashboard              # Creates app/dashboard/layout.tsx
/new-layout settings               # Creates app/settings/layout.tsx
/new-layout (marketing)            # Creates app/(marketing)/layout.tsx
/new-layout admin                  # Creates app/admin/layout.tsx
```

## How It Works

### 1. Determine Layout Purpose

Based on the layout name, infer:
- What kind of layout (authenticated, public, admin)
- What metadata to generate
- What navigation/sidebar elements to include
- Whether authentication checks are needed

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` for conventions
- `skills/new-layout/references/layout-examples.md` for examples
- Existing layouts in `src/app/` for project patterns

### 3. Generate Files

#### Layout: `src/app/<route>/layout.tsx`

```typescript
import type { Metadata } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  title: {
    template: '%s | Dashboard',
    default: 'Dashboard',
  },
  description: 'Manage your account',
};

type LayoutProps = {
  children: ReactNode;
};

export default function DashboardLayout({ children }: LayoutProps) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1">{children}</main>
    </div>
  );
}
```

#### Loading: `src/app/<route>/loading.tsx`

```typescript
export default function Loading() {
  return <LoadingSkeleton />;
}
```

#### Error: `src/app/<route>/error.tsx`

```typescript
'use client';

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function Error({ error, reset }: ErrorProps) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

### 4. Verify

Run type checking:
```bash
npx tsc --noEmit
```

## Rules

- Layouts are Server Components by default
- `loading.tsx` and `error.tsx` are automatically used by Next.js
- `error.tsx` must be a Client Component (`'use client'`)
- Use template patterns for metadata titles
- Keep layouts focused on structure, not content
- Consider authentication requirements for protected routes

## Generated Files

```
src/app/<route>/layout.tsx
src/app/<route>/loading.tsx
src/app/<route>/error.tsx
src/app/<route>/not-found.tsx (optional)
```

## Example Output

For `/new-layout dashboard`:

**Layout:** `src/app/dashboard/layout.tsx`
```typescript
import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { redirect } from 'next/navigation';
import { getCurrentUser } from '@/lib/auth';
import { DashboardSidebar } from '@/components/dashboard/Sidebar';
import { DashboardHeader } from '@/components/dashboard/Header';

export const metadata: Metadata = {
  title: {
    template: '%s | Dashboard',
    default: 'Dashboard',
  },
  description: 'Manage your account and settings',
};

type DashboardLayoutProps = {
  children: ReactNode;
};

export default async function DashboardLayout({ children }: DashboardLayoutProps) {
  const user = await getCurrentUser();

  if (!user) {
    redirect('/login');
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DashboardSidebar user={user} />
      <div className="flex flex-1 flex-col">
        <DashboardHeader user={user} />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
```

**Loading:** `src/app/dashboard/loading.tsx`
```typescript
import { Skeleton } from '@/components/ui/Skeleton';

export default function DashboardLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
      </div>
      <Skeleton className="h-96" />
    </div>
  );
}
```

**Error:** `src/app/dashboard/error.tsx`
```typescript
'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/Button';

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function DashboardError({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log error to error reporting service
    console.error('Dashboard error:', error);
  }, [error]);

  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center">
      <h2 className="mb-4 text-xl font-semibold">Something went wrong</h2>
      <p className="mb-6 text-gray-600">
        We encountered an error loading this page.
      </p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
```

**Not Found:** `src/app/dashboard/not-found.tsx`
```typescript
import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function DashboardNotFound() {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center">
      <h2 className="mb-4 text-xl font-semibold">Page not found</h2>
      <p className="mb-6 text-gray-600">
        The page you're looking for doesn't exist.
      </p>
      <Button asChild>
        <Link href="/dashboard">Go to Dashboard</Link>
      </Button>
    </div>
  );
}
```
