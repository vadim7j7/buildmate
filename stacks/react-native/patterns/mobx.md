# MobX State Management Patterns (React Native)

## Store Definition

```typescript
// stores/AuthStore.ts
import { makeAutoObservable, runInAction } from 'mobx';
import AsyncStorage from '@react-native-async-storage/async-storage';

class AuthStore {
  user: User | null = null;
  token: string | null = null;
  isLoading = false;

  constructor() {
    makeAutoObservable(this);
    this.loadFromStorage();
  }

  get isAuthenticated() {
    return !!this.token && !!this.user;
  }

  async loadFromStorage() {
    try {
      const data = await AsyncStorage.getItem('auth');
      if (data) {
        runInAction(() => {
          const parsed = JSON.parse(data);
          this.user = parsed.user;
          this.token = parsed.token;
        });
      }
    } catch (error) {
      console.error('Failed to load auth from storage:', error);
    }
  }

  async login(user: User, token: string) {
    this.user = user;
    this.token = token;
    await AsyncStorage.setItem('auth', JSON.stringify({ user, token }));
  }

  async logout() {
    this.user = null;
    this.token = null;
    await AsyncStorage.removeItem('auth');
  }

  updateUser(updates: Partial<User>) {
    if (this.user) {
      this.user = { ...this.user, ...updates };
    }
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

## Provider Setup

```typescript
// app/_layout.tsx
import { StoreContext, rootStore } from '@/stores/RootStore';

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
// screens/ProfileScreen.tsx
import { observer } from 'mobx-react-lite';
import { useStores } from '@/stores/RootStore';

export const ProfileScreen = observer(() => {
  const { authStore } = useStores();

  const handleLogout = async () => {
    await authStore.logout();
    router.replace('/login');
  };

  return (
    <View>
      <Text>{authStore.user?.name}</Text>
      <Text>{authStore.isAuthenticated ? 'Logged in' : 'Guest'}</Text>
      <Button onPress={handleLogout} title="Logout" />
    </View>
  );
});
```

## Key Patterns

1. **Use makeAutoObservable** for automatic observable detection
2. **Wrap async updates** in runInAction when not using flow
3. **Use observer HOC** on all components that read observables
4. **Use computed getters** for derived state (isAuthenticated)
5. **Root Store pattern** for dependency injection
6. **Persist to AsyncStorage** manually or with mobx-persist-store
