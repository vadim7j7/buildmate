# MobX State Management Patterns (React Native)

MobX stores hold **UI state only**. Tokens and secrets live in `expo-secure-store`
(`@/services/auth`, see `.claude/patterns/security.md`); the user profile and every
server or DB record live in TanStack Query. The session store keeps only the
session *status*. Never write a token to AsyncStorage (it is unencrypted).

## Session Store (status only)

```typescript
// src/stores/SessionStore.ts
import { makeAutoObservable, runInAction } from 'mobx';
import { getAccessToken, storeTokens, clearTokens } from '@/services/auth';
import { queryClient } from '@/queries/queryClient';

type SessionStatus = 'unknown' | 'signedIn' | 'signedOut';

export class SessionStore {
  status: SessionStatus = 'unknown';

  constructor() {
    makeAutoObservable(this);
  }

  get isSignedIn() {
    return this.status === 'signedIn';
  }

  async restore() {
    const token = await getAccessToken();              // SecureStore
    runInAction(() => {
      this.status = token ? 'signedIn' : 'signedOut';
    });
  }

  async signIn(accessToken: string, refreshToken: string) {
    await storeTokens(accessToken, refreshToken);      // SecureStore
    runInAction(() => {
      this.status = 'signedIn';
    });
  }

  async signOut() {
    await clearTokens();
    queryClient.clear();                               // drop the previous user's data
    runInAction(() => {
      this.status = 'signedOut';
    });
  }
}
```

## UI Store

```typescript
// src/stores/TransactionFilterStore.ts
import { makeAutoObservable } from 'mobx';

export class TransactionFilterStore {
  category: string | null = null;
  sortOrder: 'asc' | 'desc' = 'desc';

  constructor() {
    makeAutoObservable(this);
  }

  setCategory(category: string | null) {
    this.category = category;
  }

  toggleSortOrder() {
    this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
  }

  reset() {
    this.category = null;
    this.sortOrder = 'desc';
  }
}
```

## Root Store and Provider

```typescript
// src/stores/RootStore.ts
import { createContext, useContext } from 'react';
import { SessionStore } from './SessionStore';
import { TransactionFilterStore } from './TransactionFilterStore';

export class RootStore {
  session = new SessionStore();
  transactionFilter = new TransactionFilterStore();
}

// Tests pass a fresh `new RootStore()` through the provider
export const StoreContext = createContext<RootStore | null>(null);
export function useStores(): RootStore {
  const stores = useContext(StoreContext);
  if (!stores) throw new Error('useStores must be used inside StoreContext.Provider');
  return stores;
}
```

```typescript
// src/app/_layout.tsx
const rootStore = new RootStore();

export default function RootLayout() {
  return (
    <StoreContext.Provider value={rootStore}>
      <Stack />
    </StoreContext.Provider>
  );
}
```

## Usage with observer

```typescript
// src/app/(tabs)/profile.tsx
import { observer } from 'mobx-react-lite';

export default observer(function ProfileScreen() {
  const { t } = useTranslation();
  const { session } = useStores();
  const { data: user } = useCurrentUser();   // profile: TanStack Query, not MobX

  const handleSignOut = async () => {
    await session.signOut();
    router.replace('/login');
  };

  return (
    <View>
      <Text>{user?.name}</Text>
      <Button onPress={handleSignOut} title={t('auth.signOut')} />
    </View>
  );
});
```

## Key Patterns

1. **UI state only**: no tokens, no profile, no server records in stores
2. **Tokens in expo-secure-store**; the session store keeps only the status
3. **`makeAutoObservable`**; async updates after `await` go in `runInAction`
4. **`observer`** on every component that reads observables
5. **Classes + a root store in context**, so tests create fresh instances
6. **`reset()`** on UI stores for sign-out and test isolation
