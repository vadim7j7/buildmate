# React Native Testing Patterns

Testing patterns and conventions for React Native + Expo applications using
Jest and React Native Testing Library. All agents must follow these patterns.

---

## 1. Test File Organization

```
src/
├── components/
│   ├── TransactionCard/
│   │   ├── TransactionCard.tsx
│   │   ├── TransactionCard.test.tsx
│   │   └── index.ts
├── screens/
│   ├── TransactionListScreen.tsx
│   └── TransactionListScreen.test.tsx
├── hooks/
│   ├── useTransactions.ts
│   └── useTransactions.test.ts
├── stores/
│   ├── useTransactionStore.ts
│   └── useTransactionStore.test.ts
├── queries/
│   ├── useTransactions.ts
│   └── useTransactions.test.ts
├── db/
│   └── queries/
│       ├── transactions.ts
│       └── transactions.test.ts
└── __tests__/
    ├── integration/
    │   └── checkout-flow.test.tsx
    └── e2e/
        └── auth.e2e.ts
```

---

## 2. Component Testing

### Basic Component Test

```typescript
// components/TransactionCard/TransactionCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react-native';
import { TransactionCard } from './TransactionCard';

const mockTransaction = {
  id: '1',
  description: 'Coffee Shop',
  amount: -4.50,
  category: 'food',
  date: '2024-01-15',
};

describe('TransactionCard', () => {
  it('renders transaction details', () => {
    render(<TransactionCard transaction={mockTransaction} />);

    expect(screen.getByText('Coffee Shop')).toBeTruthy();
    expect(screen.getByText('-$4.50')).toBeTruthy();
  });

  it('shows negative amount in red', () => {
    render(<TransactionCard transaction={mockTransaction} />);

    const amount = screen.getByText('-$4.50');
    expect(amount.props.style).toEqual(
      expect.objectContaining({ color: expect.stringMatching(/red|#[fF]{2}0000/) })
    );
  });

  it('calls onPress when tapped', () => {
    const handlePress = jest.fn();

    render(
      <TransactionCard transaction={mockTransaction} onPress={handlePress} />
    );

    fireEvent.press(screen.getByText('Coffee Shop'));
    expect(handlePress).toHaveBeenCalledWith('1');
  });
});
```

### Testing with Providers

```typescript
// test-utils/render.tsx
import { render, RenderOptions } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nextProvider } from 'react-i18next';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import i18n from '@/locales/i18n';

function AllProviders({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <SafeAreaProvider>
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </I18nextProvider>
    </SafeAreaProvider>
  );
}

function customRender(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllProviders, ...options });
}

export * from '@testing-library/react-native';
export { customRender as render };
```

---

## 3. Screen Testing

```typescript
// screens/TransactionListScreen.test.tsx
import { render, screen, waitFor, fireEvent } from '@/test-utils/render';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import TransactionListScreen from './TransactionListScreen';

const mockTransactions = [
  { id: '1', description: 'Coffee', amount: -4.50 },
  { id: '2', description: 'Salary', amount: 5000 },
];

const server = setupServer(
  rest.get('*/api/transactions', (req, res, ctx) => {
    return res(ctx.json({ data: mockTransactions }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('TransactionListScreen', () => {
  it('shows loading indicator initially', () => {
    render(<TransactionListScreen />);

    expect(screen.getByTestId('loading-indicator')).toBeTruthy();
  });

  it('displays transactions after loading', async () => {
    render(<TransactionListScreen />);

    await waitFor(() => {
      expect(screen.getByText('Coffee')).toBeTruthy();
      expect(screen.getByText('Salary')).toBeTruthy();
    });
  });

  it('shows empty state when no transactions', async () => {
    server.use(
      rest.get('*/api/transactions', (req, res, ctx) => {
        return res(ctx.json({ data: [] }));
      })
    );

    render(<TransactionListScreen />);

    await waitFor(() => {
      expect(screen.getByText(/no transactions/i)).toBeTruthy();
    });
  });

  it('shows error state on fetch failure', async () => {
    server.use(
      rest.get('*/api/transactions', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );

    render(<TransactionListScreen />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeTruthy();
    });
  });

  it('refreshes on pull down', async () => {
    render(<TransactionListScreen />);

    await waitFor(() => {
      expect(screen.getByText('Coffee')).toBeTruthy();
    });

    const list = screen.getByTestId('transaction-list');
    fireEvent(list, 'refresh');

    // Verify refresh was triggered
    await waitFor(() => {
      expect(screen.getByText('Coffee')).toBeTruthy();
    });
  });
});
```

---

## 4. Form Testing

```typescript
// screens/TransactionFormScreen.test.tsx
import { render, screen, fireEvent, waitFor } from '@/test-utils/render';
import { Alert } from 'react-native';
import TransactionFormScreen from './TransactionFormScreen';

jest.spyOn(Alert, 'alert');

const mockRouterBack = jest.fn();
jest.mock('expo-router', () => ({
  router: { back: () => mockRouterBack() },
  useLocalSearchParams: () => ({}),
}));

describe('TransactionFormScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders form inputs', () => {
    render(<TransactionFormScreen />);

    expect(screen.getByPlaceholderText(/description/i)).toBeTruthy();
    expect(screen.getByPlaceholderText(/amount/i)).toBeTruthy();
  });

  it('validates required fields', async () => {
    render(<TransactionFormScreen />);

    fireEvent.press(screen.getByText(/save/i));

    await waitFor(() => {
      expect(screen.getByText(/description is required/i)).toBeTruthy();
    });
  });

  it('submits valid form data', async () => {
    const mockCreate = jest.fn().mockResolvedValue({ id: '1' });
    jest.mock('@/queries/useTransactions', () => ({
      useCreateTransaction: () => ({
        mutateAsync: mockCreate,
        isPending: false,
      }),
    }));

    render(<TransactionFormScreen />);

    fireEvent.changeText(
      screen.getByPlaceholderText(/description/i),
      'Test Transaction'
    );
    fireEvent.changeText(screen.getByPlaceholderText(/amount/i), '50.00');
    fireEvent.press(screen.getByText(/save/i));

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith({
        description: 'Test Transaction',
        amount: 50.00,
      });
      expect(mockRouterBack).toHaveBeenCalled();
    });
  });

  it('shows error alert on submission failure', async () => {
    const mockCreate = jest.fn().mockRejectedValue(new Error('Server error'));
    jest.mock('@/queries/useTransactions', () => ({
      useCreateTransaction: () => ({
        mutateAsync: mockCreate,
        isPending: false,
      }),
    }));

    render(<TransactionFormScreen />);

    fireEvent.changeText(
      screen.getByPlaceholderText(/description/i),
      'Test'
    );
    fireEvent.changeText(screen.getByPlaceholderText(/amount/i), '50');
    fireEvent.press(screen.getByText(/save/i));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        expect.any(String),
        expect.stringContaining('failed')
      );
    });
  });

  it('disables submit button while saving', async () => {
    jest.mock('@/queries/useTransactions', () => ({
      useCreateTransaction: () => ({
        mutateAsync: jest.fn(),
        isPending: true,
      }),
    }));

    render(<TransactionFormScreen />);

    const saveButton = screen.getByText(/save/i);
    expect(saveButton.props.accessibilityState?.disabled).toBe(true);
  });
});
```

---

## 5. Zustand Store Testing

```typescript
// stores/useTransactionStore.test.ts
import { act, renderHook } from '@testing-library/react-native';
import { useTransactionStore } from './useTransactionStore';

describe('useTransactionStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useTransactionStore.getState().reset();
  });

  it('initializes with default values', () => {
    const { result } = renderHook(() => useTransactionStore());

    expect(result.current.filterCategory).toBeNull();
    expect(result.current.sortOrder).toBe('desc');
    expect(result.current.isFilterVisible).toBe(false);
  });

  it('updates filter category', () => {
    const { result } = renderHook(() => useTransactionStore());

    act(() => {
      result.current.setFilterCategory('food');
    });

    expect(result.current.filterCategory).toBe('food');
  });

  it('toggles sort order', () => {
    const { result } = renderHook(() => useTransactionStore());

    expect(result.current.sortOrder).toBe('desc');

    act(() => {
      result.current.toggleSortOrder();
    });

    expect(result.current.sortOrder).toBe('asc');

    act(() => {
      result.current.toggleSortOrder();
    });

    expect(result.current.sortOrder).toBe('desc');
  });

  it('resets to initial state', () => {
    const { result } = renderHook(() => useTransactionStore());

    act(() => {
      result.current.setFilterCategory('food');
      result.current.setFilterVisible(true);
    });

    expect(result.current.filterCategory).toBe('food');

    act(() => {
      result.current.reset();
    });

    expect(result.current.filterCategory).toBeNull();
    expect(result.current.isFilterVisible).toBe(false);
  });
});
```

---

## 6. React Query Hook Testing

```typescript
// queries/useTransactions.test.ts
import { renderHook, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { useTransactions, useCreateTransaction } from './useTransactions';

const mockTransactions = [
  { id: '1', description: 'Test', amount: 100 },
];

const server = setupServer(
  rest.get('*/api/transactions', (req, res, ctx) => {
    return res(ctx.json({ data: mockTransactions }));
  }),
  rest.post('*/api/transactions', async (req, res, ctx) => {
    const body = await req.json();
    return res(ctx.json({ id: '2', ...body }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe('useTransactions', () => {
  it('fetches transactions', async () => {
    const { result } = renderHook(() => useTransactions(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockTransactions);
  });

  it('handles fetch error', async () => {
    server.use(
      rest.get('*/api/transactions', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );

    const { result } = renderHook(() => useTransactions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useCreateTransaction', () => {
  it('creates a transaction', async () => {
    const { result } = renderHook(() => useCreateTransaction(), {
      wrapper: createWrapper(),
    });

    const newTransaction = { description: 'New', amount: 50 };

    await result.current.mutateAsync(newTransaction);

    expect(result.current.data).toEqual({
      id: '2',
      ...newTransaction,
    });
  });
});
```

---

## 7. Database Query Testing

```typescript
// db/queries/transactions.test.ts
import { eq } from 'drizzle-orm';
import { db } from '../client';
import { transactions } from '../schema';
import {
  getTransactions,
  getTransactionById,
  createTransaction,
  deleteTransaction,
} from './transactions';

// Use a test database
beforeAll(async () => {
  await db.delete(transactions);  // Clean slate
});

afterEach(async () => {
  await db.delete(transactions);  // Clean up after each test
});

describe('transactions queries', () => {
  describe('getTransactions', () => {
    it('returns all transactions ordered by date', async () => {
      await db.insert(transactions).values([
        { id: '1', description: 'A', amount: 100, createdAt: new Date('2024-01-01') },
        { id: '2', description: 'B', amount: 200, createdAt: new Date('2024-01-02') },
      ]);

      const result = await getTransactions();

      expect(result).toHaveLength(2);
      expect(result[0].description).toBe('B');  // Newer first
    });
  });

  describe('getTransactionById', () => {
    it('returns transaction by id', async () => {
      await db.insert(transactions).values({
        id: '1',
        description: 'Test',
        amount: 100,
      });

      const result = await getTransactionById('1');

      expect(result?.description).toBe('Test');
    });

    it('returns null for non-existent id', async () => {
      const result = await getTransactionById('999');

      expect(result).toBeNull();
    });
  });

  describe('createTransaction', () => {
    it('creates and returns new transaction', async () => {
      const result = await createTransaction({
        description: 'New Transaction',
        amount: 50,
        category: 'food',
      });

      expect(result[0].id).toBeDefined();
      expect(result[0].description).toBe('New Transaction');
    });
  });

  describe('deleteTransaction', () => {
    it('deletes transaction by id', async () => {
      await db.insert(transactions).values({
        id: '1',
        description: 'To Delete',
        amount: 100,
      });

      await deleteTransaction('1');

      const result = await getTransactionById('1');
      expect(result).toBeNull();
    });
  });
});
```

---

## 8. Navigation Testing

```typescript
// screens/__tests__/navigation.test.tsx
import { render, screen, fireEvent } from '@/test-utils/render';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import HomeScreen from '../HomeScreen';
import DetailScreen from '../DetailScreen';

const Stack = createNativeStackNavigator();

function TestNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="Detail" component={DetailScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

describe('Navigation', () => {
  it('navigates from Home to Detail', async () => {
    render(<TestNavigator />);

    // Start on Home
    expect(screen.getByText('Home Screen')).toBeTruthy();

    // Navigate to Detail
    fireEvent.press(screen.getByText('Go to Detail'));

    // Now on Detail
    expect(screen.getByText('Detail Screen')).toBeTruthy();
  });

  it('passes params to Detail screen', async () => {
    render(<TestNavigator />);

    fireEvent.press(screen.getByText('Item 1'));

    expect(screen.getByText('Item ID: 1')).toBeTruthy();
  });
});
```

---

## 9. Async Storage Mocking

```typescript
// __mocks__/@react-native-async-storage/async-storage.ts
const storage: Record<string, string> = {};

export default {
  setItem: jest.fn((key: string, value: string) => {
    storage[key] = value;
    return Promise.resolve();
  }),
  getItem: jest.fn((key: string) => {
    return Promise.resolve(storage[key] ?? null);
  }),
  removeItem: jest.fn((key: string) => {
    delete storage[key];
    return Promise.resolve();
  }),
  clear: jest.fn(() => {
    Object.keys(storage).forEach((key) => delete storage[key]);
    return Promise.resolve();
  }),
  getAllKeys: jest.fn(() => {
    return Promise.resolve(Object.keys(storage));
  }),
};

// Usage in test
import AsyncStorage from '@react-native-async-storage/async-storage';

beforeEach(() => {
  AsyncStorage.clear();
});

it('saves theme preference', async () => {
  await saveTheme('dark');

  expect(AsyncStorage.setItem).toHaveBeenCalledWith('theme', 'dark');
});
```

---

## 10. Testing Utilities

### Factory Functions

```typescript
// test-utils/factories.ts
export function createTransaction(
  overrides: Partial<Transaction> = {}
): Transaction {
  return {
    id: Math.random().toString(36).substr(2, 9),
    description: 'Test Transaction',
    amount: 100,
    category: 'other',
    date: new Date().toISOString(),
    ...overrides,
  };
}

export function createUser(overrides: Partial<User> = {}): User {
  return {
    id: Math.random().toString(36).substr(2, 9),
    name: 'Test User',
    email: 'test@example.com',
    ...overrides,
  };
}

// Usage
const transaction = createTransaction({ amount: -50, category: 'food' });
const transactions = Array.from({ length: 10 }, () => createTransaction());
```

### Wait Utilities

```typescript
// test-utils/wait.ts
export function waitForLoadingToFinish() {
  return waitFor(() => {
    expect(screen.queryByTestId('loading-indicator')).toBeFalsy();
  });
}

export async function fillForm(fields: Record<string, string>) {
  for (const [placeholder, value] of Object.entries(fields)) {
    fireEvent.changeText(
      screen.getByPlaceholderText(new RegExp(placeholder, 'i')),
      value
    );
  }
}
```

---

## Quick Reference

| Test Type | Tool | Location |
|-----------|------|----------|
| Component | RNTL | `*.test.tsx` |
| Screen | RNTL + MSW | `screens/*.test.tsx` |
| Store (Zustand) | renderHook | `stores/*.test.ts` |
| Queries (React Query) | renderHook + MSW | `queries/*.test.ts` |
| Database | Jest | `db/queries/*.test.ts` |
| Navigation | RNTL | `__tests__/navigation.test.tsx` |
| E2E | Detox/Maestro | `e2e/*.e2e.ts` |

### Common Queries

```typescript
// By text
screen.getByText('Hello')
screen.getByText(/hello/i)  // Case insensitive

// By placeholder
screen.getByPlaceholderText('Enter email')

// By testID
screen.getByTestId('submit-button')

// By accessibility
screen.getByRole('button', { name: 'Submit' })
screen.getByLabelText('Email input')
```

### Fire Events

```typescript
// Press
fireEvent.press(element);

// Text input
fireEvent.changeText(input, 'new value');

// Scroll
fireEvent.scroll(scrollView, { nativeEvent: { contentOffset: { y: 100 } } });

// Refresh (pull-to-refresh)
fireEvent(flatList, 'refresh');
```
