# Redux Toolkit State Management Patterns (React Native)

Redux holds **UI state only**. Tokens and secrets live in `expo-secure-store`
(`@/services/auth`, see `.claude/patterns/security.md`); the user profile and every
server or DB record live in TanStack Query. The `session` slice keeps only the
session *status*. Don't use redux-persist for auth: AsyncStorage is unencrypted, and
a persisted copy of server data goes stale. Persist only non-sensitive preferences.

## Store Setup

```typescript
// src/store/index.ts
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import sessionReducer from './slices/sessionSlice';
import transactionFilterReducer from './slices/transactionFilterSlice';

// Exported so tests can build a fresh store from the same reducers
export const rootReducer = combineReducers({
  session: sessionReducer,
  transactionFilter: transactionFilterReducer,
});

export function makeStore(preloadedState?: Partial<RootState>) {
  return configureStore({ reducer: rootReducer, preloadedState });
}

export const store = makeStore();
export type RootState = ReturnType<typeof rootReducer>;
export type AppDispatch = typeof store.dispatch;
```

## Session Slice (status only)

```typescript
// src/store/slices/sessionSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { getAccessToken, storeTokens, clearTokens } from '@/services/auth';
import { queryClient } from '@/queries/queryClient';

type SessionStatus = 'unknown' | 'signedIn' | 'signedOut';

export const restoreSession = createAsyncThunk('session/restore', async () =>
  Boolean(await getAccessToken())                      // SecureStore
);

export const signIn = createAsyncThunk(
  'session/signIn',
  async (tokens: { accessToken: string; refreshToken: string }) => {
    await storeTokens(tokens.accessToken, tokens.refreshToken); // SecureStore, not the state
  }
);

export const signOut = createAsyncThunk('session/signOut', async () => {
  await clearTokens();
  queryClient.clear();                                 // drop the previous user's data
});

const sessionSlice = createSlice({
  name: 'session',
  initialState: { status: 'unknown' as SessionStatus },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(restoreSession.fulfilled, (state, action) => {
        state.status = action.payload ? 'signedIn' : 'signedOut';
      })
      .addCase(signIn.fulfilled, (state) => { state.status = 'signedIn'; })
      .addCase(signOut.fulfilled, (state) => { state.status = 'signedOut'; });
  },
});

export default sessionSlice.reducer;
```

## UI Slice

```typescript
// src/store/slices/transactionFilterSlice.ts
import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

const initialState = {
  category: null as string | null,
  sortOrder: 'desc' as 'asc' | 'desc',
};

const transactionFilterSlice = createSlice({
  name: 'transactionFilter',
  initialState,
  reducers: {
    setCategory: (state, action: PayloadAction<string | null>) => {
      state.category = action.payload;
    },
    toggleSortOrder: (state) => {
      state.sortOrder = state.sortOrder === 'asc' ? 'desc' : 'asc';
    },
    reset: () => initialState,
  },
});

export const { setCategory, toggleSortOrder, reset } = transactionFilterSlice.actions;
export default transactionFilterSlice.reducer;
```

## Typed Hooks

```typescript
// src/store/hooks.ts
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from './index';

export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppSelector = useSelector.withTypes<RootState>();
```

## Provider Setup

```typescript
// src/app/_layout.tsx
import { Provider } from 'react-redux';
import { store } from '@/store';

export default function RootLayout() {
  return (
    <Provider store={store}>
      <Stack />
    </Provider>
  );
}
```

## Usage in Components

```typescript
// src/app/(tabs)/profile.tsx
export default function ProfileScreen() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { data: user } = useCurrentUser();   // profile: TanStack Query, not Redux

  const handleSignOut = async () => {
    await dispatch(signOut());
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

The root layout dispatches `restoreSession()` once and guards routes with
`<Stack.Protected guard={status === 'signedIn'}>`, where
`status = useAppSelector((s) => s.session.status)`.

## Key Patterns

1. **UI state only**: no tokens, no user profile, no server records in slices
2. **Tokens in expo-secure-store**, written from thunks; slices keep the status
3. **`createSlice`** (Immer) and a `reset` reducer per UI slice
4. **Typed hooks** via `useDispatch.withTypes` / `useSelector.withTypes`
5. **`makeStore()` + exported `rootReducer`** so each test gets a fresh store
6. **Narrow selectors**; derive with `createSelector` instead of returning new objects
