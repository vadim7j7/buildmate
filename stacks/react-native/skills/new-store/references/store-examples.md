# Zustand Store Examples

## Basic UI State Store

A simple store for filter and sort UI state.

```typescript
// stores/useTransactionFilterStore.ts
import { create } from 'zustand';

// 1. Define the state interface (state + actions)
interface TransactionFilterState {
  // State
  filterCategory: string | null;
  sortOrder: 'asc' | 'desc';
  searchQuery: string;
  isFilterVisible: boolean;

  // Actions
  setFilterCategory: (category: string | null) => void;
  toggleSortOrder: () => void;
  setSearchQuery: (query: string) => void;
  setFilterVisible: (visible: boolean) => void;
  reset: () => void;
}

// 2. Extract initial state for reset()
const initialState = {
  filterCategory: null as string | null,
  sortOrder: 'desc' as const,
  searchQuery: '',
  isFilterVisible: false,
};

// 3. Create the store
export const useTransactionFilterStore = create<TransactionFilterState>()(
  (set) => ({
    ...initialState,

    setFilterCategory: (category) => set({ filterCategory: category }),

    toggleSortOrder: () =>
      set((state) => ({
        sortOrder: state.sortOrder === 'asc' ? 'desc' : 'asc',
      })),

    setSearchQuery: (query) => set({ searchQuery: query }),

    setFilterVisible: (visible) => set({ isFilterVisible: visible }),

    // 4. Reset restores initial state
    reset: () => set(initialState),
  })
);

// 5. Export selector hooks for fine-grained subscriptions
export const useFilterCategory = () =>
  useTransactionFilterStore((s) => s.filterCategory);

export const useSortOrder = () =>
  useTransactionFilterStore((s) => s.sortOrder);

export const useSearchQuery = () =>
  useTransactionFilterStore((s) => s.searchQuery);

export const useIsFilterVisible = () =>
  useTransactionFilterStore((s) => s.isFilterVisible);
```

---

## App-Level Store

A store for global app state like theme, locale, and onboarding.

```typescript
// stores/useAppStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

type Theme = 'light' | 'dark' | 'system';

interface AppState {
  // State
  theme: Theme;
  locale: string;
  hasCompletedOnboarding: boolean;
  lastSyncTimestamp: number | null;

  // Actions
  setTheme: (theme: Theme) => void;
  setLocale: (locale: string) => void;
  completeOnboarding: () => void;
  setLastSyncTimestamp: (timestamp: number) => void;
  reset: () => void;
}

const initialState = {
  theme: 'system' as Theme,
  locale: 'en',
  hasCompletedOnboarding: false,
  lastSyncTimestamp: null as number | null,
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      ...initialState,

      setTheme: (theme) => set({ theme }),
      setLocale: (locale) => set({ locale }),
      completeOnboarding: () => set({ hasCompletedOnboarding: true }),
      setLastSyncTimestamp: (timestamp) =>
        set({ lastSyncTimestamp: timestamp }),
      reset: () => set(initialState),
    }),
    {
      name: 'app-store',
      storage: createJSONStorage(() => AsyncStorage),
      // Only persist certain fields
      partialize: (state) => ({
        theme: state.theme,
        locale: state.locale,
        hasCompletedOnboarding: state.hasCompletedOnboarding,
      }),
    }
  )
);

// Selector hooks
export const useTheme = () => useAppStore((s) => s.theme);
export const useLocale = () => useAppStore((s) => s.locale);
export const useHasCompletedOnboarding = () =>
  useAppStore((s) => s.hasCompletedOnboarding);
```

---

## Form Draft Store

A store for holding form draft state before submission.

```typescript
// stores/useBudgetFormStore.ts
import { create } from 'zustand';

interface BudgetFormState {
  // Form fields
  name: string;
  amount: string; // String for input field; parse on submit
  category: string;
  period: 'weekly' | 'monthly' | 'yearly';

  // UI state
  isDirty: boolean;
  hasSubmitted: boolean;

  // Actions
  setName: (name: string) => void;
  setAmount: (amount: string) => void;
  setCategory: (category: string) => void;
  setPeriod: (period: 'weekly' | 'monthly' | 'yearly') => void;
  markSubmitted: () => void;
  reset: () => void;
}

const initialState = {
  name: '',
  amount: '',
  category: 'other',
  period: 'monthly' as const,
  isDirty: false,
  hasSubmitted: false,
};

export const useBudgetFormStore = create<BudgetFormState>()((set) => ({
  ...initialState,

  setName: (name) => set({ name, isDirty: true }),
  setAmount: (amount) => set({ amount, isDirty: true }),
  setCategory: (category) => set({ category, isDirty: true }),
  setPeriod: (period) => set({ period, isDirty: true }),
  markSubmitted: () => set({ hasSubmitted: true }),
  reset: () => set(initialState),
}));

// Selector hooks
export const useBudgetFormName = () => useBudgetFormStore((s) => s.name);
export const useBudgetFormAmount = () => useBudgetFormStore((s) => s.amount);
export const useBudgetFormCategory = () =>
  useBudgetFormStore((s) => s.category);
export const useBudgetFormPeriod = () => useBudgetFormStore((s) => s.period);
export const useBudgetFormIsDirty = () => useBudgetFormStore((s) => s.isDirty);

// Validation helper (not in store, derived)
export function validateBudgetForm(state: Pick<BudgetFormState, 'name' | 'amount'>) {
  const errors: Record<string, string> = {};
  if (!state.name.trim()) errors.name = 'Name is required';
  const amount = parseFloat(state.amount);
  if (isNaN(amount) || amount <= 0) errors.amount = 'Amount must be positive';
  return errors;
}
```

---

## Multi-Select Store

A store for managing multi-select state in a list.

```typescript
// stores/useSelectionStore.ts
import { create } from 'zustand';

interface SelectionState {
  selectedIds: Set<string>;
  isSelecting: boolean;

  toggleSelection: (id: string) => void;
  selectAll: (ids: string[]) => void;
  clearSelection: () => void;
  startSelecting: () => void;
  stopSelecting: () => void;
  reset: () => void;
}

const initialState = {
  selectedIds: new Set<string>(),
  isSelecting: false,
};

export const useSelectionStore = create<SelectionState>()((set) => ({
  ...initialState,

  toggleSelection: (id) =>
    set((state) => {
      const newSet = new Set(state.selectedIds);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return {
        selectedIds: newSet,
        isSelecting: newSet.size > 0,
      };
    }),

  selectAll: (ids) =>
    set({
      selectedIds: new Set(ids),
      isSelecting: true,
    }),

  clearSelection: () =>
    set({
      selectedIds: new Set<string>(),
      isSelecting: false,
    }),

  startSelecting: () => set({ isSelecting: true }),
  stopSelecting: () =>
    set({ isSelecting: false, selectedIds: new Set<string>() }),

  reset: () => set({ ...initialState, selectedIds: new Set<string>() }),
}));

// Selector hooks
export const useSelectedIds = () => useSelectionStore((s) => s.selectedIds);
export const useIsSelecting = () => useSelectionStore((s) => s.isSelecting);
export const useSelectedCount = () =>
  useSelectionStore((s) => s.selectedIds.size);
export const useIsSelected = (id: string) =>
  useSelectionStore((s) => s.selectedIds.has(id));
```

---

## Testing Pattern for All Stores

Every store test follows this pattern:

```typescript
// __tests__/stores/useTransactionFilterStore.test.ts
import { useTransactionFilterStore } from '@/stores/useTransactionFilterStore';

describe('useTransactionFilterStore', () => {
  // CRITICAL: Reset before every test
  beforeEach(() => {
    useTransactionFilterStore.getState().reset();
  });

  describe('initial state', () => {
    it('has null filter category', () => {
      expect(useTransactionFilterStore.getState().filterCategory).toBeNull();
    });

    it('has desc sort order', () => {
      expect(useTransactionFilterStore.getState().sortOrder).toBe('desc');
    });

    it('has empty search query', () => {
      expect(useTransactionFilterStore.getState().searchQuery).toBe('');
    });

    it('has filter hidden', () => {
      expect(useTransactionFilterStore.getState().isFilterVisible).toBe(false);
    });
  });

  describe('actions', () => {
    it('sets filter category', () => {
      useTransactionFilterStore.getState().setFilterCategory('food');
      expect(useTransactionFilterStore.getState().filterCategory).toBe('food');
    });

    it('toggles sort order', () => {
      useTransactionFilterStore.getState().toggleSortOrder();
      expect(useTransactionFilterStore.getState().sortOrder).toBe('asc');
    });

    it('sets search query', () => {
      useTransactionFilterStore.getState().setSearchQuery('groceries');
      expect(useTransactionFilterStore.getState().searchQuery).toBe('groceries');
    });
  });

  describe('reset', () => {
    it('restores initial state', () => {
      useTransactionFilterStore.getState().setFilterCategory('food');
      useTransactionFilterStore.getState().toggleSortOrder();
      useTransactionFilterStore.getState().setSearchQuery('test');
      useTransactionFilterStore.getState().setFilterVisible(true);

      useTransactionFilterStore.getState().reset();

      const state = useTransactionFilterStore.getState();
      expect(state.filterCategory).toBeNull();
      expect(state.sortOrder).toBe('desc');
      expect(state.searchQuery).toBe('');
      expect(state.isFilterVisible).toBe(false);
    });
  });
});
```
