# React Context Examples

## Example 1: Auth Context

Full authentication context with login, logout, and user state.

```typescript
// src/contexts/AuthContext.tsx
'use client';

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
  type ReactNode,
} from 'react';
import { useRouter } from 'next/navigation';
import { loginApi, logoutApi, fetchCurrentUserApi } from '@/services/auth';

type User = {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'member' | 'viewer';
};

type LoginCredentials = {
  email: string;
  password: string;
};

type AuthContextValue = {
  /** The current authenticated user, or null if not logged in */
  user: User | null;
  /** Whether the auth state is being initialized */
  loading: boolean;
  /** Whether the user is authenticated */
  isAuthenticated: boolean;
  /** Log in with email and password */
  login: (credentials: LoginCredentials) => Promise<void>;
  /** Log out and redirect to login page */
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    (async () => {
      try {
        const currentUser = await fetchCurrentUserApi();
        setUser(currentUser);
      } catch {
        // Not authenticated - that's fine
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      const response = await loginApi(credentials);
      setUser(response.user);
      router.push('/dashboard');
    },
    [router]
  );

  const logout = useCallback(async () => {
    try {
      await logoutApi();
    } finally {
      setUser(null);
      router.push('/login');
    }
  }, [router]);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: user !== null,
      login,
      logout,
    }),
    [user, loading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access auth context. Must be used within an AuthProvider.
 * @throws Error if used outside of AuthProvider
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

```typescript
// src/contexts/AuthContext.test.tsx
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from './AuthContext';
import * as authService from '@/services/auth';

jest.mock('@/services/auth');
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

const mockFetchCurrentUser = authService.fetchCurrentUserApi as jest.MockedFunction<
  typeof authService.fetchCurrentUserApi
>;
const mockLogin = authService.loginApi as jest.MockedFunction<typeof authService.loginApi>;
const mockLogout = authService.logoutApi as jest.MockedFunction<typeof authService.logoutApi>;

// Test component that uses the context
function TestConsumer() {
  const { user, isAuthenticated, loading, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="loading">{loading.toString()}</span>
      <span data-testid="authenticated">{isAuthenticated.toString()}</span>
      <span data-testid="user">{user?.name ?? 'none'}</span>
      <button onClick={() => login({ email: 'test@test.com', password: 'pass' })}>Login</button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it('throws when useAuth is used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    expect(() => render(<TestConsumer />)).toThrow(
      'useAuth must be used within an AuthProvider'
    );

    consoleSpy.mockRestore();
  });

  it('initializes with loading state', () => {
    mockFetchCurrentUser.mockReturnValue(new Promise(() => {}));

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    expect(screen.getByTestId('loading')).toHaveTextContent('true');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
  });

  it('loads existing user session', async () => {
    const user = { id: '1', name: 'John', email: 'john@test.com', role: 'member' as const };
    mockFetchCurrentUser.mockResolvedValue(user);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
      expect(screen.getByTestId('user')).toHaveTextContent('John');
    });
  });

  it('handles login', async () => {
    mockFetchCurrentUser.mockRejectedValue(new Error('Not authenticated'));
    mockLogin.mockResolvedValue({
      user: { id: '1', name: 'John', email: 'john@test.com' },
      token: 'tok',
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });

    await act(async () => {
      await userEvent.click(screen.getByText('Login'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    });
  });
});
```

---

## Example 2: Theme Context

Toggle between light and dark themes with persistence.

```typescript
// src/contexts/ThemeContext.tsx
'use client';

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
  type ReactNode,
} from 'react';

type ThemeMode = 'light' | 'dark';

type ThemeContextValue = {
  /** Current theme mode */
  mode: ThemeMode;
  /** Toggle between light and dark */
  toggle: () => void;
  /** Set a specific theme mode */
  setMode: (mode: ThemeMode) => void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const STORAGE_KEY = 'theme-mode';

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>('light');

  // Load saved theme on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
    if (saved === 'light' || saved === 'dark') {
      setModeState(saved);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setModeState('dark');
    }
  }, []);

  const setMode = useCallback((newMode: ThemeMode) => {
    setModeState(newMode);
    localStorage.setItem(STORAGE_KEY, newMode);
  }, []);

  const toggle = useCallback(() => {
    setMode(mode === 'light' ? 'dark' : 'light');
  }, [mode, setMode]);

  const value = useMemo(() => ({ mode, toggle, setMode }), [mode, toggle, setMode]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
```

---

## Example 3: Workspace Context

Manages the currently selected workspace/organization.

```typescript
// src/contexts/WorkspaceContext.tsx
'use client';

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
  type ReactNode,
} from 'react';
import { fetchWorkspacesApi } from '@/services/workspaces';

type Workspace = {
  id: string;
  name: string;
  slug: string;
  role: 'owner' | 'admin' | 'member';
};

type WorkspaceContextValue = {
  /** List of all workspaces the user belongs to */
  workspaces: Workspace[];
  /** The currently active workspace */
  currentWorkspace: Workspace | null;
  /** Whether workspaces are loading */
  loading: boolean;
  /** Switch to a different workspace */
  switchWorkspace: (workspaceId: string) => void;
};

const WorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchWorkspacesApi();
        setWorkspaces(data);
        // Default to first workspace or saved preference
        const savedId = localStorage.getItem('current-workspace');
        const defaultId = savedId && data.find((w) => w.id === savedId) ? savedId : data[0]?.id;
        setCurrentId(defaultId ?? null);
      } catch {
        // Handle error silently - workspaces will be empty
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const switchWorkspace = useCallback(
    (workspaceId: string) => {
      const workspace = workspaces.find((w) => w.id === workspaceId);
      if (workspace) {
        setCurrentId(workspaceId);
        localStorage.setItem('current-workspace', workspaceId);
      }
    },
    [workspaces]
  );

  const currentWorkspace = useMemo(
    () => workspaces.find((w) => w.id === currentId) ?? null,
    [workspaces, currentId]
  );

  const value = useMemo(
    () => ({ workspaces, currentWorkspace, loading, switchWorkspace }),
    [workspaces, currentWorkspace, loading, switchWorkspace]
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
}
```

---

## Context Integration in Layout

```typescript
// src/app/layout.tsx
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { WorkspaceProvider } from '@/contexts/WorkspaceContext';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <MantineProvider>
          <Notifications position="top-right" />
          <AuthProvider>
            <ThemeProvider>
              <WorkspaceProvider>
                {children}
              </WorkspaceProvider>
            </ThemeProvider>
          </AuthProvider>
        </MantineProvider>
      </body>
    </html>
  );
}
```

---

## Key Patterns Summary

1. **`createContext` with `undefined`**: Always use `createContext<T | undefined>(undefined)`
2. **Custom hook with guard**: Always throw if context is undefined
3. **`useMemo` on value**: Prevents unnecessary re-renders of consumers
4. **`useCallback` on handlers**: Stabilizes function references
5. **IIFE async in `useEffect`**: For initialization data fetching
6. **`type` not `interface`**: Follows project convention
