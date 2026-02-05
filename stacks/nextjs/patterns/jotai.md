# Jotai State Management Patterns (Next.js)

## Basic Atoms

```typescript
// atoms/auth.ts
import { atom } from 'jotai';

export const userAtom = atom<User | null>(null);
export const isLoadingAtom = atom(false);

// Derived atoms (computed)
export const isAuthenticatedAtom = atom((get) => {
  return !!get(userAtom);
});

export const userNameAtom = atom((get) => {
  return get(userAtom)?.name ?? 'Guest';
});
```

## Write-Only Atoms (Actions)

```typescript
// atoms/auth.ts
export const fetchUserAtom = atom(null, async (get, set) => {
  set(isLoadingAtom, true);
  try {
    const response = await fetch('/api/auth/me');
    const user = await response.json();
    set(userAtom, user);
  } finally {
    set(isLoadingAtom, false);
  }
});

export const logoutAtom = atom(null, (get, set) => {
  set(userAtom, null);
});
```

## Async Atoms

```typescript
// atoms/user.ts
import { atom } from 'jotai';
import { atomWithQuery } from 'jotai-tanstack-query';

// Simple async atom
export const userProfileAtom = atom(async () => {
  const response = await fetch('/api/user/profile');
  return response.json();
});

// With TanStack Query integration
export const userQueryAtom = atomWithQuery(() => ({
  queryKey: ['user'],
  queryFn: async () => {
    const response = await fetch('/api/user/profile');
    return response.json();
  },
}));
```

## Provider Setup (App Router)

```typescript
// app/providers.tsx
'use client';

import { Provider } from 'jotai';

export function JotaiProvider({ children }: { children: React.ReactNode }) {
  return <Provider>{children}</Provider>;
}
```

```typescript
// app/layout.tsx
import { JotaiProvider } from './providers';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <JotaiProvider>{children}</JotaiProvider>
      </body>
    </html>
  );
}
```

## Usage in Components

```typescript
// components/UserProfile.tsx
'use client';

import { useAtom, useAtomValue, useSetAtom } from 'jotai';
import { userAtom, isAuthenticatedAtom, logoutAtom, fetchUserAtom } from '@/atoms/auth';
import { useEffect } from 'react';

export function UserProfile() {
  // Read-only
  const user = useAtomValue(userAtom);
  const isAuthenticated = useAtomValue(isAuthenticatedAtom);

  // Write-only
  const logout = useSetAtom(logoutAtom);
  const fetchUser = useSetAtom(fetchUserAtom);

  useEffect(() => {
    if (!user) {
      fetchUser();
    }
  }, [user, fetchUser]);

  return (
    <div>
      <p>{user?.name ?? 'Guest'}</p>
      <p>{isAuthenticated ? 'Logged in' : 'Not logged in'}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

## Atom with Storage (localStorage)

```typescript
// atoms/settings.ts
import { atomWithStorage } from 'jotai/utils';

export const themeAtom = atomWithStorage<'light' | 'dark'>('theme', 'light');
export const sidebarOpenAtom = atomWithStorage('sidebarOpen', true);
```

## Atom Families

```typescript
// atoms/items.ts
import { atomFamily } from 'jotai/utils';

export const itemAtomFamily = atomFamily((id: string) =>
  atom<Item | null>(null)
);

// Usage
const itemAtom = itemAtomFamily('item-123');
const [item, setItem] = useAtom(itemAtom);
```

## Key Patterns

1. **Use derived atoms** for computed values
2. **Use write-only atoms** for actions
3. **Use useAtomValue** for read-only access
4. **Use useSetAtom** for write-only access (better perf)
5. **Use atomWithStorage** for localStorage persistence
6. **Use atomFamily** for dynamic atoms
7. **Mark components as 'use client'**
8. **Integrate with TanStack Query** via jotai-tanstack-query
