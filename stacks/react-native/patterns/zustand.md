# Zustand State Management Patterns (React Native)

Zustand holds **UI state only**. Where everything else lives:

| Data | Lives in |
|---|---|
| Access / refresh tokens, secrets | `expo-secure-store` via `@/services/auth` (`.claude/patterns/security.md`) |
| The signed-in user's profile, any server or DB record | TanStack Query (`src/queries/`) |
| Session *status* (unknown / signed in / signed out), filters, sheets, drafts | Zustand |
| Non-sensitive preferences (theme, onboarding done) | Zustand + `persist` (AsyncStorage) |

Never persist a token or a server record through Zustand's `persist`: AsyncStorage is
unencrypted, and a persisted copy of server data goes stale.

## Session Store (status only, tokens in SecureStore)

```typescript
// src/stores/useSessionStore.ts
import { create } from 'zustand';
import { getAccessToken, storeTokens, clearTokens } from '@/services/auth';
import { queryClient } from '@/queries/queryClient';

type SessionStatus = 'unknown' | 'signedIn' | 'signedOut';

interface SessionState {
  status: SessionStatus;
  restore: () => Promise<void>;
  signIn: (accessToken: string, refreshToken: string) => Promise<void>;
  signOut: () => Promise<void>;
}

export const useSessionStore = create<SessionState>()((set) => ({
  status: 'unknown',
  restore: async () => {
    const token = await getAccessToken();          // SecureStore
    set({ status: token ? 'signedIn' : 'signedOut' });
  },
  signIn: async (accessToken, refreshToken) => {
    await storeTokens(accessToken, refreshToken);  // SecureStore
    set({ status: 'signedIn' });
  },
  signOut: async () => {
    await clearTokens();
    queryClient.clear();                           // drop the previous user's cached data
    set({ status: 'signedOut' });
  },
}));

export const useSessionStatus = () => useSessionStore((s) => s.status);
```

The profile comes from a query, not the store:

```typescript
// src/queries/useCurrentUser.ts
export function useCurrentUser() {
  const status = useSessionStatus();
  return useQuery({
    queryKey: queryKeys.currentUser,
    queryFn: fetchCurrentUser,          // the API client reads the token from SecureStore
    enabled: status === 'signedIn',
  });
}
```

## UI State Store (Non-Persisted)

```typescript
// src/stores/useTransactionFilterStore.ts
import { create } from 'zustand';

interface TransactionFilterState {
  category: string | null;
  sortOrder: 'asc' | 'desc';
  isFilterSheetOpen: boolean;
  setCategory: (category: string | null) => void;
  toggleSortOrder: () => void;
  setFilterSheetOpen: (open: boolean) => void;
  reset: () => void;
}

const initialState = {
  category: null,
  sortOrder: 'desc' as const,
  isFilterSheetOpen: false,
};

export const useTransactionFilterStore = create<TransactionFilterState>()((set) => ({
  ...initialState,
  setCategory: (category) => set({ category }),
  toggleSortOrder: () =>
    set((s) => ({ sortOrder: s.sortOrder === 'asc' ? 'desc' : 'asc' })),
  setFilterSheetOpen: (isFilterSheetOpen) => set({ isFilterSheetOpen }),
  reset: () => set(initialState),
}));

// Selector hooks: components subscribe to single values
export const useFilterCategory = () => useTransactionFilterStore((s) => s.category);
```

## Persisted Preferences (non-sensitive only)

```typescript
// src/stores/usePreferencesStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface PreferencesState {
  theme: 'system' | 'light' | 'dark';
  hasSeenOnboarding: boolean;
  setTheme: (theme: PreferencesState['theme']) => void;
  completeOnboarding: () => void;
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      theme: 'system',
      hasSeenOnboarding: false,
      setTheme: (theme) => set({ theme }),
      completeOnboarding: () => set({ hasSeenOnboarding: true }),
    }),
    { name: 'preferences', storage: createJSONStorage(() => AsyncStorage) }
  )
);
```

## Usage in Components

```typescript
// src/app/(tabs)/profile.tsx
export default function ProfileScreen() {
  const { t } = useTranslation();
  const { data: user } = useCurrentUser();                 // server data: Query
  const signOut = useSessionStore((s) => s.signOut);        // action: store

  const handleSignOut = async () => {
    await signOut();
    router.replace('/login');
  };

  return (
    <View>
      <Text>{user?.name}</Text>
      <Button onPress={handleSignOut} title={t('auth.signOut')} />
    </View>
  );
}
```

Route guarding reads `useSessionStatus()` in the root layout
(`<Stack.Protected guard={status === 'signedIn'}>`) and calls `restore()` once on
start-up, keeping the splash screen up while the status is `'unknown'`.

## Key Patterns

1. **UI state only**: no server records, no tokens, no user profile in a store
2. **Tokens in expo-secure-store**; the store keeps only the session status
3. **Selector hooks** so components subscribe to single values
4. **`reset()` action** on UI stores, for sign-out and test isolation
5. **`persist` only for non-sensitive preferences**
6. **Clear the Query cache on sign-out** so the next user never sees old data
