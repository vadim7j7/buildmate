# React Native Jest Testing Patterns

## Setup and Configuration

### Jest Config for Expo

```javascript
// jest.config.js
module.exports = {
  preset: 'jest-expo',
  setupFilesAfterEnv: ['./jest.setup.ts'],
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg|@shopify/flash-list)',
  ],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  collectCoverageFrom: [
    'components/**/*.{ts,tsx}',
    'app/**/*.{ts,tsx}',
    'stores/**/*.{ts,tsx}',
    'queries/**/*.{ts,tsx}',
    'db/queries/**/*.{ts,tsx}',
    'hooks/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
};
```

### Jest Setup File

```typescript
// jest.setup.ts
import '@testing-library/react-native/extend-expect';

// Silence React Native logs in tests
jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');

// Mock expo-router globally
jest.mock('expo-router', () => ({
  useLocalSearchParams: jest.fn(() => ({})),
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    back: jest.fn(),
    replace: jest.fn(),
    canGoBack: jest.fn(() => true),
  })),
  router: {
    push: jest.fn(),
    back: jest.fn(),
    replace: jest.fn(),
    canGoBack: jest.fn(() => true),
  },
  Link: ({ children, ...props }: any) => children,
  Stack: {
    Screen: () => null,
  },
  Tabs: {
    Screen: () => null,
  },
  useFocusEffect: jest.fn((cb) => cb()),
  useNavigation: jest.fn(() => ({
    setOptions: jest.fn(),
  })),
}));

// Mock react-i18next globally
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      if (params) {
        return `${key}:${JSON.stringify(params)}`;
      }
      return key;
    },
    i18n: {
      changeLanguage: jest.fn(),
      language: 'en',
    },
  }),
  Trans: ({ children }: { children: React.ReactNode }) => children,
  initReactI18next: { type: '3rdParty', init: jest.fn() },
}));

// Mock expo-image
jest.mock('expo-image', () => ({
  Image: 'Image',
}));
```

---

## Component Test Pattern

Test that a component renders correctly, handles props, and responds to user
interactions.

```typescript
// __tests__/components/TransactionCard.test.tsx
import { render, fireEvent, screen } from '@testing-library/react-native';
import { TransactionCard } from '@/components/lists/TransactionCard';

const mockTransaction = {
  id: '1',
  description: 'Grocery shopping',
  amount: -45.99,
  category: 'food',
  createdAt: new Date('2026-01-15'),
};

describe('TransactionCard', () => {
  it('renders transaction details', () => {
    render(<TransactionCard transaction={mockTransaction} />);

    expect(screen.getByText('Grocery shopping')).toBeTruthy();
    expect(screen.getByText('-$45.99')).toBeTruthy();
  });

  it('calls onPress handler when tapped', () => {
    const onPress = jest.fn();
    render(
      <TransactionCard transaction={mockTransaction} onPress={onPress} />
    );

    fireEvent.press(screen.getByText('Grocery shopping'));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('does not crash when onPress is not provided', () => {
    render(<TransactionCard transaction={mockTransaction} />);
    // Should not throw
    fireEvent.press(screen.getByText('Grocery shopping'));
  });

  it('renders different styles for income vs expense', () => {
    const income = { ...mockTransaction, amount: 100 };
    const { rerender } = render(<TransactionCard transaction={income} />);
    const incomeAmount = screen.getByText('$100.00');

    rerender(<TransactionCard transaction={mockTransaction} />);
    const expenseAmount = screen.getByText('-$45.99');

    // Verify they have different styling
    expect(incomeAmount.props.style).not.toEqual(expenseAmount.props.style);
  });
});
```

---

## Screen Test Pattern

Test that a screen loads data, renders content, handles loading and error states,
and integrates with navigation.

```typescript
// __tests__/screens/TransactionsScreen.test.tsx
import { render, waitFor, fireEvent, screen } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TransactionsScreen from '@/app/(tabs)/transactions';
import { getTransactions } from '@/db/queries/transactions';
import { useTransactionStore } from '@/stores/useTransactionStore';

// Mock database layer
jest.mock('@/db/queries/transactions', () => ({
  getTransactions: jest.fn(),
  createTransaction: jest.fn(),
}));

const mockTransactions = [
  { id: '1', description: 'Groceries', amount: -50, createdAt: new Date() },
  { id: '2', description: 'Salary', amount: 3000, createdAt: new Date() },
];

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
}

function renderScreen() {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <TransactionsScreen />
    </QueryClientProvider>
  );
}

describe('TransactionsScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useTransactionStore.getState().reset();
  });

  it('shows loading state while fetching data', () => {
    // Return a promise that never resolves to keep loading state
    (getTransactions as jest.Mock).mockReturnValue(new Promise(() => {}));
    renderScreen();
    // The screen should render without crashing during loading
    expect(screen.getByTestId('transactions-screen')).toBeTruthy();
  });

  it('renders transactions after successful fetch', async () => {
    (getTransactions as jest.Mock).mockResolvedValue(mockTransactions);
    renderScreen();

    await waitFor(() => {
      expect(screen.getByText('Groceries')).toBeTruthy();
      expect(screen.getByText('Salary')).toBeTruthy();
    });
  });

  it('displays empty state when no transactions exist', async () => {
    (getTransactions as jest.Mock).mockResolvedValue([]);
    renderScreen();

    await waitFor(() => {
      expect(screen.getByText('transactions.empty')).toBeTruthy();
    });
  });

  it('shows error state on fetch failure', async () => {
    (getTransactions as jest.Mock).mockRejectedValue(new Error('Network error'));
    renderScreen();

    await waitFor(() => {
      expect(screen.getByText('common.error')).toBeTruthy();
    });
  });

  it('refreshes data on pull-to-refresh', async () => {
    (getTransactions as jest.Mock).mockResolvedValue(mockTransactions);
    renderScreen();

    await waitFor(() => {
      expect(screen.getByText('Groceries')).toBeTruthy();
    });

    // Simulate pull-to-refresh
    const list = screen.getByTestId('transactions-list');
    fireEvent(list, 'refresh');

    expect(getTransactions).toHaveBeenCalledTimes(2);
  });
});
```

---

## Zustand Store Test Pattern

Test store state transitions, actions, and the reset mechanism. Always reset
before each test.

```typescript
// __tests__/stores/useTransactionStore.test.ts
import { useTransactionStore } from '@/stores/useTransactionStore';

describe('useTransactionStore', () => {
  beforeEach(() => {
    // CRITICAL: Reset store state before every test
    useTransactionStore.getState().reset();
  });

  describe('initial state', () => {
    it('has null filter category', () => {
      expect(useTransactionStore.getState().filterCategory).toBeNull();
    });

    it('has desc sort order', () => {
      expect(useTransactionStore.getState().sortOrder).toBe('desc');
    });

    it('has filter hidden', () => {
      expect(useTransactionStore.getState().isFilterVisible).toBe(false);
    });
  });

  describe('setFilterCategory', () => {
    it('sets the filter category', () => {
      useTransactionStore.getState().setFilterCategory('food');
      expect(useTransactionStore.getState().filterCategory).toBe('food');
    });

    it('clears the filter category with null', () => {
      useTransactionStore.getState().setFilterCategory('food');
      useTransactionStore.getState().setFilterCategory(null);
      expect(useTransactionStore.getState().filterCategory).toBeNull();
    });
  });

  describe('toggleSortOrder', () => {
    it('toggles from desc to asc', () => {
      useTransactionStore.getState().toggleSortOrder();
      expect(useTransactionStore.getState().sortOrder).toBe('asc');
    });

    it('toggles from asc back to desc', () => {
      useTransactionStore.getState().toggleSortOrder(); // asc
      useTransactionStore.getState().toggleSortOrder(); // desc
      expect(useTransactionStore.getState().sortOrder).toBe('desc');
    });
  });

  describe('reset', () => {
    it('restores all values to initial state', () => {
      // Modify everything
      useTransactionStore.getState().setFilterCategory('food');
      useTransactionStore.getState().toggleSortOrder();
      useTransactionStore.getState().setFilterVisible(true);

      // Reset
      useTransactionStore.getState().reset();

      // Verify
      const state = useTransactionStore.getState();
      expect(state.filterCategory).toBeNull();
      expect(state.sortOrder).toBe('desc');
      expect(state.isFilterVisible).toBe(false);
    });
  });
});
```

---

## React Query Hook Test Pattern

Test query hooks with a fresh QueryClient per test. Always mock the data layer.

```typescript
// __tests__/queries/useTransactions.test.ts
import { renderHook, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTransactions, useCreateTransaction } from '@/queries/useTransactions';
import {
  getTransactions,
  createTransaction,
} from '@/db/queries/transactions';

jest.mock('@/db/queries/transactions');

const mockData = [
  { id: '1', description: 'Test', amount: 100, createdAt: new Date() },
];

function createWrapper() {
  // CRITICAL: Fresh QueryClient for every test
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
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
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns data on successful fetch', async () => {
    (getTransactions as jest.Mock).mockResolvedValue(mockData);

    const { result } = renderHook(() => useTransactions(), {
      wrapper: createWrapper(),
    });

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockData);
  });

  it('returns error on failed fetch', async () => {
    (getTransactions as jest.Mock).mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useTransactions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error?.message).toBe('fail');
  });
});

describe('useCreateTransaction', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('calls createTransaction with provided data', async () => {
    const input = { description: 'New', amount: 50 };
    (createTransaction as jest.Mock).mockResolvedValue({ id: '2', ...input });

    const { result } = renderHook(() => useCreateTransaction(), {
      wrapper: createWrapper(),
    });

    await result.current.mutateAsync(input);

    expect(createTransaction).toHaveBeenCalledWith(input);
  });
});
```

---

## Form Input Test Pattern

Test controlled inputs, validation, and user interactions.

```typescript
// __tests__/components/TextInput.test.tsx
import { render, fireEvent, screen } from '@testing-library/react-native';
import { TextInput } from '@/components/ui/TextInput';

describe('TextInput', () => {
  it('renders label and placeholder', () => {
    render(
      <TextInput
        label="Email"
        value=""
        onChangeText={jest.fn()}
        placeholder="you@example.com"
        testID="email-input"
      />
    );

    expect(screen.getByText('Email')).toBeTruthy();
    expect(screen.getByPlaceholderText('you@example.com')).toBeTruthy();
  });

  it('calls onChangeText with new value', () => {
    const onChangeText = jest.fn();
    render(
      <TextInput
        label="Email"
        value=""
        onChangeText={onChangeText}
        testID="email-input"
      />
    );

    fireEvent.changeText(screen.getByTestId('email-input'), 'test@test.com');
    expect(onChangeText).toHaveBeenCalledWith('test@test.com');
  });

  it('displays error message', () => {
    render(
      <TextInput
        label="Email"
        value="bad"
        onChangeText={jest.fn()}
        error="Invalid email format"
      />
    );

    expect(screen.getByText('Invalid email format')).toBeTruthy();
  });

  it('applies error styling when error is present', () => {
    const { getByTestId } = render(
      <TextInput
        label="Email"
        value=""
        onChangeText={jest.fn()}
        error="Required"
        testID="email-input"
      />
    );

    const input = getByTestId('email-input');
    // The input should have error-related styling applied
    expect(input.props.style).toBeDefined();
  });
});
```

---

## Loading and Error State Test Pattern

```typescript
// __tests__/components/StateScreens.test.tsx
import { render, fireEvent, screen } from '@testing-library/react-native';
import { LoadingScreen } from '@/components/ui/LoadingScreen';
import { ErrorScreen } from '@/components/ui/ErrorScreen';
import { EmptyState } from '@/components/ui/EmptyState';

describe('LoadingScreen', () => {
  it('renders an activity indicator', () => {
    render(<LoadingScreen />);
    expect(screen.getByTestId('loading-indicator')).toBeTruthy();
  });

  it('shows a custom loading message', () => {
    render(<LoadingScreen message="Syncing data..." />);
    expect(screen.getByText('Syncing data...')).toBeTruthy();
  });
});

describe('ErrorScreen', () => {
  it('renders the error message', () => {
    render(<ErrorScreen message="Connection lost" />);
    expect(screen.getByText('Connection lost')).toBeTruthy();
  });

  it('shows retry button when onRetry is provided', () => {
    const onRetry = jest.fn();
    render(<ErrorScreen message="Error" onRetry={onRetry} />);

    fireEvent.press(screen.getByText('common.retry'));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('hides retry button when onRetry is not provided', () => {
    render(<ErrorScreen message="Error" />);
    expect(screen.queryByText('common.retry')).toBeNull();
  });
});

describe('EmptyState', () => {
  it('renders the empty message', () => {
    render(<EmptyState message="No items found" />);
    expect(screen.getByText('No items found')).toBeTruthy();
  });

  it('renders action button when onAction is provided', () => {
    const onAction = jest.fn();
    render(
      <EmptyState
        message="No items"
        actionLabel="Add Item"
        onAction={onAction}
      />
    );

    fireEvent.press(screen.getByText('Add Item'));
    expect(onAction).toHaveBeenCalledTimes(1);
  });
});
```
