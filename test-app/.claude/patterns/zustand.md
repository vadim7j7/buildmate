# Zustand State Management Patterns

## Overview

Zustand is a lightweight state management library. Use it for client-side UI state only. Server data should use React Query.

## Store Structure

```
src/
  stores/
    useAuthStore.ts      # Authentication state
    useUIStore.ts        # UI state (modals, sidebars)
    useCartStore.ts      # Shopping cart (if e-commerce)
```

## Basic Store Pattern

```typescript
// stores/useCounterStore.ts
import { create } from 'zustand'

interface CounterState {
  count: number
  increment: () => void
  decrement: () => void
  reset: () => void
}

export const useCounterStore = create<CounterState>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
  reset: () => set({ count: 0 }),
}))
```

## Usage in Components

```tsx
// Select only what you need (prevents unnecessary re-renders)
const count = useCounterStore((state) => state.count)
const increment = useCounterStore((state) => state.increment)

// Or use shallow comparison for multiple selectors
import { shallow } from 'zustand/shallow'

const { count, increment } = useCounterStore(
  (state) => ({ count: state.count, increment: state.increment }),
  shallow
)
```

## Store with Async Actions

```typescript
// stores/useUserStore.ts
import { create } from 'zustand'

interface UserState {
  user: User | null
  isLoading: boolean
  error: string | null
  fetchUser: (id: string) => Promise<void>
  logout: () => void
}

export const useUserStore = create<UserState>((set) => ({
  user: null,
  isLoading: false,
  error: null,

  fetchUser: async (id) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/users/${id}`)
      const user = await response.json()
      set({ user, isLoading: false })
    } catch (error) {
      set({ error: 'Failed to fetch user', isLoading: false })
    }
  },

  logout: () => set({ user: null }),
}))
```

## Persisted Store

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SettingsState {
  theme: 'light' | 'dark'
  setTheme: (theme: 'light' | 'dark') => void
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'light',
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'settings-storage', // localStorage key
    }
  )
)
```

## Slices Pattern (Large Stores)

```typescript
// stores/slices/authSlice.ts
export interface AuthSlice {
  isAuthenticated: boolean
  login: () => void
  logout: () => void
}

export const createAuthSlice = (set: any): AuthSlice => ({
  isAuthenticated: false,
  login: () => set({ isAuthenticated: true }),
  logout: () => set({ isAuthenticated: false }),
})

// stores/slices/uiSlice.ts
export interface UISlice {
  isSidebarOpen: boolean
  toggleSidebar: () => void
}

export const createUISlice = (set: any): UISlice => ({
  isSidebarOpen: false,
  toggleSidebar: () => set((state: any) => ({ isSidebarOpen: !state.isSidebarOpen })),
})

// stores/useAppStore.ts
import { create } from 'zustand'
import { createAuthSlice, AuthSlice } from './slices/authSlice'
import { createUISlice, UISlice } from './slices/uiSlice'

export const useAppStore = create<AuthSlice & UISlice>()((...a) => ({
  ...createAuthSlice(...a),
  ...createUISlice(...a),
}))
```

## Reset Store

```typescript
const initialState = {
  count: 0,
  name: '',
}

export const useStore = create<State>((set) => ({
  ...initialState,
  // ... actions
  reset: () => set(initialState),
}))
```

## Best Practices

1. **One store per domain** - Don't put everything in one giant store
2. **Select specific state** - Use selectors to prevent unnecessary re-renders
3. **Keep actions in store** - Don't dispatch actions from components
4. **Use TypeScript** - Always type your stores
5. **Server state belongs elsewhere** - Use React Query for API data
6. **Persist sparingly** - Only persist what truly needs to survive refresh
