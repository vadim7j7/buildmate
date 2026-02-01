# React Query Hook Examples

## Complete Query Hook Module

A full module with list query, detail query, and CRUD mutations.

```typescript
// queries/useBudgets.ts
import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import {
  getBudgets,
  getBudgetById,
  createBudget,
  updateBudget,
  deleteBudget,
} from '@/db/queries/budgets';
import { queryKeys } from './queryKeys';
import type { NewBudget } from '@/db/schema';

// --- Queries ---

/**
 * Fetch all budgets.
 */
export function useBudgets() {
  return useQuery({
    queryKey: queryKeys.budgets.all,
    queryFn: getBudgets,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Fetch a single budget by ID.
 * Disabled when id is empty/undefined.
 */
export function useBudget(id: string) {
  return useQuery({
    queryKey: queryKeys.budgets.detail(id),
    queryFn: () => getBudgetById(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Fetch budgets with filters.
 */
export function useBudgetsByCategory(category: string | null) {
  return useQuery({
    queryKey: queryKeys.budgets.list({ category }),
    queryFn: () => getBudgets({ category }),
    enabled: category !== null,
    staleTime: 5 * 60 * 1000,
  });
}

// --- Mutations ---

/**
 * Create a new budget.
 * Invalidates the budget list on success.
 */
export function useCreateBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: NewBudget) => createBudget(data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.budgets.all,
      });
    },
  });
}

/**
 * Update an existing budget.
 * Invalidates both the list and the specific detail cache.
 */
export function useUpdateBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { id: string } & Partial<NewBudget>) =>
      updateBudget(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.budgets.all,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.budgets.detail(variables.id),
      });
    },
  });
}

/**
 * Delete a budget.
 * Invalidates the budget list on success.
 */
export function useDeleteBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteBudget(id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.budgets.all,
      });
    },
  });
}
```

---

## Query Key Factory

Centralised query key management. All keys follow a hierarchical pattern.

```typescript
// queries/queryKeys.ts
export const queryKeys = {
  budgets: {
    all: ['budgets'] as const,
    lists: () => [...queryKeys.budgets.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.budgets.lists(), filters] as const,
    details: () => [...queryKeys.budgets.all, 'detail'] as const,
    detail: (id: string) =>
      [...queryKeys.budgets.details(), id] as const,
  },
  transactions: {
    all: ['transactions'] as const,
    lists: () => [...queryKeys.transactions.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.transactions.lists(), filters] as const,
    details: () => [...queryKeys.transactions.all, 'detail'] as const,
    detail: (id: string) =>
      [...queryKeys.transactions.details(), id] as const,
  },
  categories: {
    all: ['categories'] as const,
  },
};
```

### Why This Pattern?

The hierarchical key structure enables targeted invalidation:

```typescript
// Invalidate everything related to budgets
queryClient.invalidateQueries({ queryKey: queryKeys.budgets.all });

// Invalidate only budget lists (not details)
queryClient.invalidateQueries({ queryKey: queryKeys.budgets.lists() });

// Invalidate a specific budget detail
queryClient.invalidateQueries({ queryKey: queryKeys.budgets.detail('123') });
```

---

## Optimistic Update Pattern

For mutations that should update the UI immediately before the server confirms.

```typescript
// queries/useTransactions.ts
export function useUpdateTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateTransaction,

    // Optimistic update
    onMutate: async (variables) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({
        queryKey: queryKeys.transactions.all,
      });

      // Snapshot previous value
      const previousTransactions = queryClient.getQueryData(
        queryKeys.transactions.all
      );

      // Optimistically update the cache
      queryClient.setQueryData(
        queryKeys.transactions.all,
        (old: Transaction[] | undefined) =>
          old?.map((t) =>
            t.id === variables.id ? { ...t, ...variables } : t
          ) ?? []
      );

      return { previousTransactions };
    },

    // Rollback on error
    onError: (_err, _variables, context) => {
      if (context?.previousTransactions) {
        queryClient.setQueryData(
          queryKeys.transactions.all,
          context.previousTransactions
        );
      }
    },

    // Refetch after error or success
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.transactions.all,
      });
    },
  });
}
```

---

## Infinite Query Pattern

For paginated lists with load-more functionality.

```typescript
// queries/useTransactionsInfinite.ts
import { useInfiniteQuery } from '@tanstack/react-query';
import { getTransactionsPaginated } from '@/db/queries/transactions';
import { queryKeys } from './queryKeys';

const PAGE_SIZE = 20;

export function useTransactionsInfinite() {
  return useInfiniteQuery({
    queryKey: [...queryKeys.transactions.all, 'infinite'],
    queryFn: ({ pageParam = 0 }) =>
      getTransactionsPaginated({ offset: pageParam, limit: PAGE_SIZE }),
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.length < PAGE_SIZE) return undefined;
      return allPages.flat().length;
    },
    initialPageParam: 0,
    staleTime: 2 * 60 * 1000,
  });
}

// Usage in a screen:
// const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
//   useTransactionsInfinite();
// const transactions = data?.pages.flat() ?? [];
```

---

## Dependent Query Pattern

When one query depends on the result of another.

```typescript
// queries/useBudgetTransactions.ts
export function useBudgetTransactions(budgetId: string) {
  // First, get the budget to know its category
  const { data: budget } = useBudget(budgetId);

  // Then, fetch transactions for that category
  return useQuery({
    queryKey: queryKeys.transactions.list({ budgetId, category: budget?.category }),
    queryFn: () =>
      getTransactionsByCategory(budget!.category),
    // Only run when budget data is available
    enabled: !!budget?.category,
    staleTime: 2 * 60 * 1000,
  });
}
```

---

## Query Hook Testing Pattern

```typescript
// __tests__/queries/useBudgets.test.ts
import { renderHook, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useBudgets, useCreateBudget } from '@/queries/useBudgets';
import { getBudgets, createBudget } from '@/db/queries/budgets';

jest.mock('@/db/queries/budgets');

const mockBudgets = [
  { id: '1', name: 'Food', amount: 500, category: 'food', spent: 320 },
  { id: '2', name: 'Transport', amount: 200, category: 'transport', spent: 80 },
];

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('useBudgets', () => {
  beforeEach(() => jest.clearAllMocks());

  it('fetches budgets successfully', async () => {
    (getBudgets as jest.Mock).mockResolvedValue(mockBudgets);

    const { result } = renderHook(() => useBudgets(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockBudgets);
  });

  it('handles fetch error', async () => {
    (getBudgets as jest.Mock).mockRejectedValue(new Error('DB error'));

    const { result } = renderHook(() => useBudgets(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe('DB error');
  });
});

describe('useCreateBudget', () => {
  beforeEach(() => jest.clearAllMocks());

  it('calls createBudget with data', async () => {
    const input = { name: 'Savings', amount: 1000, category: 'savings' };
    (createBudget as jest.Mock).mockResolvedValue({ id: '3', ...input });

    const { result } = renderHook(() => useCreateBudget(), {
      wrapper: createWrapper(),
    });

    await result.current.mutateAsync(input);
    expect(createBudget).toHaveBeenCalledWith(input);
  });
});
```
