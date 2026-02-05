# Jotai State Management Patterns (React Native)

## Basic Atoms

```typescript
// atoms/auth.ts
import { atom } from 'jotai';
import { atomWithStorage, createJSONStorage } from 'jotai/utils';
import AsyncStorage from '@react-native-async-storage/async-storage';

const storage = createJSONStorage(() => AsyncStorage);

// Persisted atoms
export const userAtom = atomWithStorage<User | null>('user', null, storage);
export const tokenAtom = atomWithStorage<string | null>('token', null, storage);

// Derived atoms (computed)
export const isAuthenticatedAtom = atom((get) => {
  const user = get(userAtom);
  const token = get(tokenAtom);
  return !!user && !!token;
});
```

## Write-Only Atoms (Actions)

```typescript
// atoms/auth.ts
export const loginAtom = atom(
  null, // no read value
  async (get, set, { user, token }: { user: User; token: string }) => {
    set(userAtom, user);
    set(tokenAtom, token);
  }
);

export const logoutAtom = atom(null, async (get, set) => {
  set(userAtom, null);
  set(tokenAtom, null);
});

export const updateUserAtom = atom(
  null,
  (get, set, updates: Partial<User>) => {
    const currentUser = get(userAtom);
    if (currentUser) {
      set(userAtom, { ...currentUser, ...updates });
    }
  }
);
```

## Async Atoms

```typescript
// atoms/user.ts
import { atom } from 'jotai';
import { atomWithQuery } from 'jotai-tanstack-query';

// Async atom with TanStack Query integration
export const userProfileAtom = atomWithQuery((get) => ({
  queryKey: ['userProfile', get(tokenAtom)],
  queryFn: async ({ queryKey: [, token] }) => {
    if (!token) return null;
    const response = await api.getProfile(token);
    return response.data;
  },
  enabled: !!get(tokenAtom),
}));
```

## Provider Setup

```typescript
// app/_layout.tsx
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
// screens/ProfileScreen.tsx
import { useAtom, useAtomValue, useSetAtom } from 'jotai';
import { userAtom, logoutAtom, isAuthenticatedAtom } from '@/atoms/auth';

export function ProfileScreen() {
  // Read-only
  const user = useAtomValue(userAtom);
  const isAuthenticated = useAtomValue(isAuthenticatedAtom);

  // Write-only
  const logout = useSetAtom(logoutAtom);

  const handleLogout = async () => {
    await logout();
    router.replace('/login');
  };

  return (
    <View>
      <Text>{user?.name}</Text>
      <Text>{isAuthenticated ? 'Logged in' : 'Guest'}</Text>
      <Button onPress={handleLogout} title="Logout" />
    </View>
  );
}
```

## Atom Families (Dynamic Atoms)

```typescript
// atoms/items.ts
import { atomFamily } from 'jotai/utils';

// Create atoms dynamically based on ID
export const itemAtomFamily = atomFamily((id: string) =>
  atom<Item | null>(null)
);

// Usage
const itemAtom = itemAtomFamily('item-123');
const [item, setItem] = useAtom(itemAtom);
```

## Key Patterns

1. **Use atomWithStorage** for persistent state
2. **Create derived atoms** for computed values
3. **Use write-only atoms** for actions
4. **Use useAtomValue** for read-only access
5. **Use useSetAtom** for write-only access
6. **Use atomFamily** for dynamic/parameterized atoms
7. **Integrate with TanStack Query** via jotai-tanstack-query
