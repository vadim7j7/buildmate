# MobX State Management Patterns (Next.js)

## Store Definition

```typescript
// stores/AuthStore.ts
import { makeAutoObservable, runInAction } from 'mobx';

class AuthStore {
  user: User | null = null;
  isLoading = false;
  error: string | null = null;

  constructor() {
    makeAutoObservable(this);
  }

  get isAuthenticated() {
    return !!this.user;
  }

  async fetchUser() {
    this.isLoading = true;
    this.error = null;
    try {
      const response = await fetch('/api/auth/me');
      const data = await response.json();
      runInAction(() => {
        this.user = data;
        this.isLoading = false;
      });
    } catch (error) {
      runInAction(() => {
        this.error = 'Failed to fetch user';
        this.isLoading = false;
      });
    }
  }

  setUser(user: User) {
    this.user = user;
  }

  logout() {
    this.user = null;
  }
}

export const authStore = new AuthStore();
```

## Root Store Pattern

```typescript
// stores/RootStore.ts
import { authStore } from './AuthStore';
import { uiStore } from './UIStore';
import { createContext, useContext } from 'react';

class RootStore {
  authStore = authStore;
  uiStore = uiStore;
}

export const rootStore = new RootStore();
export const StoreContext = createContext(rootStore);
export const useStores = () => useContext(StoreContext);
```

## Provider Setup (App Router)

```typescript
// app/providers.tsx
'use client';

import { StoreContext, rootStore } from '@/stores/RootStore';
import { enableStaticRendering } from 'mobx-react-lite';

// Prevent memory leaks on server
enableStaticRendering(typeof window === 'undefined');

export function StoreProvider({ children }: { children: React.ReactNode }) {
  return (
    <StoreContext.Provider value={rootStore}>
      {children}
    </StoreContext.Provider>
  );
}
```

```typescript
// app/layout.tsx
import { StoreProvider } from './providers';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <StoreProvider>{children}</StoreProvider>
      </body>
    </html>
  );
}
```

## Usage with observer

```typescript
// components/UserProfile.tsx
'use client';

import { observer } from 'mobx-react-lite';
import { useStores } from '@/stores/RootStore';
import { useEffect } from 'react';

export const UserProfile = observer(() => {
  const { authStore } = useStores();

  useEffect(() => {
    if (!authStore.user && !authStore.isLoading) {
      authStore.fetchUser();
    }
  }, [authStore]);

  if (authStore.isLoading) return <div>Loading...</div>;
  if (authStore.error) return <div>Error: {authStore.error}</div>;

  return (
    <div>
      <p>{authStore.user?.name}</p>
      <p>{authStore.isAuthenticated ? 'Logged in' : 'Guest'}</p>
      <button onClick={() => authStore.logout()}>Logout</button>
    </div>
  );
});
```

## Local Observable State

```typescript
// components/Counter.tsx
'use client';

import { observer, useLocalObservable } from 'mobx-react-lite';

export const Counter = observer(() => {
  const state = useLocalObservable(() => ({
    count: 0,
    increment() {
      this.count++;
    },
    decrement() {
      this.count--;
    },
  }));

  return (
    <div>
      <p>Count: {state.count}</p>
      <button onClick={() => state.increment()}>+</button>
      <button onClick={() => state.decrement()}>-</button>
    </div>
  );
});
```

## Key Patterns

1. **Use makeAutoObservable** for automatic observable detection
2. **Wrap async updates** in runInAction
3. **Use observer HOC** on all components that read observables
4. **Use computed getters** for derived state
5. **Call enableStaticRendering** for SSR compatibility
6. **Use useLocalObservable** for component-local state
7. **Mark components as 'use client'**
