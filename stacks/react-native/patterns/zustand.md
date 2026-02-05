# Zustand State Management Patterns (React Native)

## Store Definition

```typescript
// stores/useAuthStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
```

## UI State Store (Non-Persisted)

```typescript
// stores/useUIStore.ts
import { create } from 'zustand';

interface UIState {
  isLoading: boolean;
  bottomSheetVisible: boolean;
  activeTab: string;
  setLoading: (loading: boolean) => void;
  showBottomSheet: () => void;
  hideBottomSheet: () => void;
  setActiveTab: (tab: string) => void;
  reset: () => void;
}

const initialState = {
  isLoading: false,
  bottomSheetVisible: false,
  activeTab: 'home',
};

export const useUIStore = create<UIState>((set) => ({
  ...initialState,
  setLoading: (isLoading) => set({ isLoading }),
  showBottomSheet: () => set({ bottomSheetVisible: true }),
  hideBottomSheet: () => set({ bottomSheetVisible: false }),
  setActiveTab: (activeTab) => set({ activeTab }),
  reset: () => set(initialState),
}));
```

## Selector Hooks

```typescript
// stores/useAuthStore.ts - add selectors
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useToken = () => useAuthStore((state) => state.token);
```

## Usage in Components

```typescript
// screens/ProfileScreen.tsx
import { useUser, useAuthStore } from '@/stores/useAuthStore';

export function ProfileScreen() {
  // Use selector for derived state (prevents unnecessary re-renders)
  const user = useUser();

  // Get actions directly from store
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = () => {
    logout();
    router.replace('/login');
  };

  return (
    <View>
      <Text>{user?.name}</Text>
      <Button onPress={handleLogout} title="Logout" />
    </View>
  );
}
```

## Key Patterns

1. **Persist sensitive data** with AsyncStorage middleware
2. **Create selector hooks** to prevent unnecessary re-renders
3. **Keep UI state separate** from domain state
4. **Add reset() action** for logout/cleanup scenarios
5. **Use immer middleware** for complex nested updates if needed
