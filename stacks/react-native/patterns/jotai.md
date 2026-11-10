# Jotai State Management Patterns (React Native)

Atoms hold **UI state only**. Tokens and secrets live in `expo-secure-store`
(`@/services/auth`, see `.claude/patterns/security.md`); the user profile and every
server or DB record live in TanStack Query. Never put a token in `atomWithStorage`:
it writes to AsyncStorage, which is unencrypted. `atomWithStorage` is for
non-sensitive preferences only.

## Session Atoms (status only)

```typescript
// src/atoms/session.ts
import { atom } from 'jotai';
import { getAccessToken, storeTokens, clearTokens } from '@/services/auth';
import { queryClient } from '@/queries/queryClient';

type SessionStatus = 'unknown' | 'signedIn' | 'signedOut';

export const sessionStatusAtom = atom<SessionStatus>('unknown');

// Write-only action atoms
export const restoreSessionAtom = atom(null, async (_get, set) => {
  const token = await getAccessToken();                    // SecureStore
  set(sessionStatusAtom, token ? 'signedIn' : 'signedOut');
});

export const signInAtom = atom(
  null,
  async (_get, set, tokens: { accessToken: string; refreshToken: string }) => {
    await storeTokens(tokens.accessToken, tokens.refreshToken);
    set(sessionStatusAtom, 'signedIn');
  }
);

export const signOutAtom = atom(null, async (_get, set) => {
  await clearTokens();
  queryClient.clear();                                     // drop the previous user's data
  set(sessionStatusAtom, 'signedOut');
});
```

The profile is a TanStack Query hook (`useCurrentUser`, enabled when
`useAtomValue(sessionStatusAtom) === 'signedIn'`), not an atom.

## UI Atoms

```typescript
// src/atoms/transactionFilter.ts
import { atom } from 'jotai';

export const filterCategoryAtom = atom<string | null>(null);
export const sortOrderAtom = atom<'asc' | 'desc'>('desc');

// Derived (read-only)
export const hasActiveFilterAtom = atom((get) => get(filterCategoryAtom) !== null);

// Write-only reset for sign-out
export const resetTransactionFilterAtom = atom(null, (_get, set) => {
  set(filterCategoryAtom, null);
  set(sortOrderAtom, 'desc');
});
```

## Persisted Preferences (non-sensitive only)

```typescript
// src/atoms/preferences.ts
import { atomWithStorage, createJSONStorage } from 'jotai/utils';
import AsyncStorage from '@react-native-async-storage/async-storage';

const storage = createJSONStorage<'system' | 'light' | 'dark'>(() => AsyncStorage);
export const themeAtom = atomWithStorage('theme', 'system', storage);
```

## Provider Setup

```typescript
// src/app/_layout.tsx
import { Provider } from 'jotai';

export default function RootLayout() {
  return (
    <Provider>
      <Stack />
    </Provider>
  );
}
```

## Usage in Components

```typescript
// src/app/(tabs)/profile.tsx
import { useSetAtom } from 'jotai';
import { signOutAtom } from '@/atoms/session';

export default function ProfileScreen() {
  const { t } = useTranslation();
  const { data: user } = useCurrentUser();     // server data: Query
  const signOut = useSetAtom(signOutAtom);

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

## Key Patterns

1. **UI state only**: no tokens, no profile, no server records in atoms
2. **Tokens in expo-secure-store**; atoms keep only the session status
3. **One atom per value**, derived atoms for computed values
4. **Write-only atoms** for actions (sign-in, sign-out, reset)
5. **`useAtomValue` / `useSetAtom`** to read or write only what a component needs
6. **`atomWithStorage` only for non-sensitive preferences**
