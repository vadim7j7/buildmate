# Next.js Layout Examples

Reference examples for generating Next.js layouts.

## Root Layout

```typescript
// src/app/layout.tsx
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from '@/components/Providers';
import '@/styles/globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: {
    template: '%s | MyApp',
    default: 'MyApp - Build Amazing Things',
  },
  description: 'The best platform for building amazing things',
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3000'),
  openGraph: {
    type: 'website',
    locale: 'en_US',
    siteName: 'MyApp',
  },
  twitter: {
    card: 'summary_large_image',
  },
};

type RootLayoutProps = {
  children: React.ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

## Marketing Layout (Group)

```typescript
// src/app/(marketing)/layout.tsx
import type { ReactNode } from 'react';
import { Header } from '@/components/marketing/Header';
import { Footer } from '@/components/marketing/Footer';

type MarketingLayoutProps = {
  children: ReactNode;
};

export default function MarketingLayout({ children }: MarketingLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
```

## Dashboard Layout (Authenticated)

```typescript
// src/app/dashboard/layout.tsx
import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { redirect } from 'next/navigation';
import { getCurrentUser } from '@/lib/auth';
import { DashboardSidebar } from '@/components/dashboard/Sidebar';
import { DashboardHeader } from '@/components/dashboard/Header';
import { DashboardProvider } from '@/contexts/DashboardContext';

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
    <DashboardProvider user={user}>
      <div className="flex min-h-screen bg-gray-50 dark:bg-gray-900">
        <DashboardSidebar />
        <div className="flex flex-1 flex-col lg:pl-64">
          <DashboardHeader />
          <main className="flex-1 p-6">{children}</main>
        </div>
      </div>
    </DashboardProvider>
  );
}
```

## Admin Layout (Role-Based)

```typescript
// src/app/admin/layout.tsx
import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { redirect, notFound } from 'next/navigation';
import { getCurrentUser } from '@/lib/auth';
import { AdminSidebar } from '@/components/admin/Sidebar';
import { AdminHeader } from '@/components/admin/Header';

export const metadata: Metadata = {
  title: {
    template: '%s | Admin',
    default: 'Admin Dashboard',
  },
  robots: {
    index: false,
    follow: false,
  },
};

type AdminLayoutProps = {
  children: ReactNode;
};

export default async function AdminLayout({ children }: AdminLayoutProps) {
  const user = await getCurrentUser();

  if (!user) {
    redirect('/login?callbackUrl=/admin');
  }

  if (!user.isAdmin) {
    notFound();
  }

  return (
    <div className="flex min-h-screen bg-gray-100">
      <AdminSidebar />
      <div className="flex flex-1 flex-col">
        <AdminHeader user={user} />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  );
}
```

## Settings Layout (Nested)

```typescript
// src/app/dashboard/settings/layout.tsx
import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { SettingsNav } from '@/components/settings/SettingsNav';

export const metadata: Metadata = {
  title: 'Settings',
};

type SettingsLayoutProps = {
  children: ReactNode;
};

export default function SettingsLayout({ children }: SettingsLayoutProps) {
  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold">Settings</h1>
      <div className="flex flex-col gap-6 lg:flex-row">
        <aside className="w-full lg:w-48">
          <SettingsNav />
        </aside>
        <div className="flex-1">{children}</div>
      </div>
    </div>
  );
}
```

## Loading States

```typescript
// src/app/dashboard/loading.tsx
import { Skeleton } from '@/components/ui/Skeleton';

export default function DashboardLoading() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-10 w-32" />
      </div>

      {/* Stats grid skeleton */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-lg" />
        ))}
      </div>

      {/* Table skeleton */}
      <div className="rounded-lg border">
        <div className="border-b p-4">
          <Skeleton className="h-6 w-32" />
        </div>
        <div className="p-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="mb-4 h-12 last:mb-0" />
          ))}
        </div>
      </div>
    </div>
  );
}
```

## Error Boundaries

```typescript
// src/app/dashboard/error.tsx
'use client';

import { useEffect } from 'react';
import * as Sentry from '@sentry/nextjs';
import { Button } from '@/components/ui/Button';
import { AlertTriangle } from 'lucide-react';

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function DashboardError({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Report to error tracking
    Sentry.captureException(error);
  }, [error]);

  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center text-center">
      <div className="mb-4 rounded-full bg-red-100 p-3">
        <AlertTriangle className="h-6 w-6 text-red-600" />
      </div>
      <h2 className="mb-2 text-xl font-semibold">Something went wrong</h2>
      <p className="mb-6 max-w-md text-gray-600">
        We encountered an unexpected error. Our team has been notified.
      </p>
      <div className="flex gap-4">
        <Button onClick={reset}>Try again</Button>
        <Button variant="outline" asChild>
          <a href="/dashboard">Go to Dashboard</a>
        </Button>
      </div>
      {error.digest && (
        <p className="mt-4 text-xs text-gray-400">Error ID: {error.digest}</p>
      )}
    </div>
  );
}
```

## Not Found Pages

```typescript
// src/app/dashboard/not-found.tsx
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { FileQuestion } from 'lucide-react';

export default function DashboardNotFound() {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center text-center">
      <div className="mb-4 rounded-full bg-gray-100 p-3">
        <FileQuestion className="h-6 w-6 text-gray-600" />
      </div>
      <h2 className="mb-2 text-xl font-semibold">Page not found</h2>
      <p className="mb-6 max-w-md text-gray-600">
        Sorry, we couldn't find the page you're looking for.
      </p>
      <Button asChild>
        <Link href="/dashboard">Back to Dashboard</Link>
      </Button>
    </div>
  );
}
```

## Global Not Found

```typescript
// src/app/not-found.tsx
import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <h1 className="mb-2 text-6xl font-bold">404</h1>
      <h2 className="mb-4 text-xl text-gray-600">Page not found</h2>
      <p className="mb-8 max-w-md text-center text-gray-500">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Button asChild>
        <Link href="/">Go Home</Link>
      </Button>
    </div>
  );
}
```

## Global Error

```typescript
// src/app/global-error.tsx
'use client';

import { useEffect } from 'react';
import * as Sentry from '@sentry/nextjs';

type GlobalErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html>
      <body>
        <div className="flex min-h-screen flex-col items-center justify-center">
          <h2 className="mb-4 text-xl font-semibold">Something went wrong!</h2>
          <button
            onClick={reset}
            className="rounded bg-blue-600 px-4 py-2 text-white"
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
```

## Parallel Routes Layout

```typescript
// src/app/dashboard/layout.tsx
import type { ReactNode } from 'react';
import { DashboardSidebar } from '@/components/dashboard/Sidebar';

type DashboardLayoutProps = {
  children: ReactNode;
  modal: ReactNode;
  notifications: ReactNode;
};

export default function DashboardLayout({
  children,
  modal,
  notifications,
}: DashboardLayoutProps) {
  return (
    <div className="flex min-h-screen">
      <DashboardSidebar />
      <div className="flex-1">
        <div className="fixed right-4 top-4 z-50">{notifications}</div>
        <main className="p-6">{children}</main>
        {modal}
      </div>
    </div>
  );
}
```

## Template (Fresh Instance)

```typescript
// src/app/dashboard/template.tsx
// Use template.tsx when you need fresh component instance on navigation
import type { ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

type TemplateProps = {
  children: ReactNode;
};

export default function DashboardTemplate({ children }: TemplateProps) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.2 }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
```
