# React Native + Expo Code Patterns

Reference patterns for code generation based on React Native + Expo conventions.
All agents and skills should follow these patterns when generating code.

---

## Pattern 1: Screen with Data Loading

A tab screen using expo-router, FlashList, React Query, and i18n for a data list.

```typescript
// app/(tabs)/transactions.tsx
import { View, Text, StyleSheet, Platform } from 'react-native';
import { Stack, Link, router } from 'expo-router';
import { FlashList } from '@shopify/flash-list';
import { useTranslation } from 'react-i18next';
import { useTransactions } from '@/queries/useTransactions';
import { TransactionCard } from '@/components/lists/TransactionCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { FloatingActionButton } from '@/components/ui/FloatingActionButton';
import { colors, spacing } from '@/constants';

export default function TransactionsScreen() {
  const { t } = useTranslation();
  const { data: transactions, isLoading, refetch } = useTransactions();

  return (
    <View style={styles.container}>
      <Stack.Screen
        options={{
          title: t('transactions.title'),
          ...(Platform.OS === 'ios' && {
            headerRight: () => (
              <Link href="/transactions/new">
                <Text style={styles.headerButton}>{t('common.add')}</Text>
              </Link>
            ),
          }),
        }}
      />
      <FlashList
        data={transactions ?? []}
        renderItem={({ item }) => <TransactionCard transaction={item} />}
        estimatedItemSize={72}
        onRefresh={refetch}
        refreshing={isLoading}
        ListEmptyComponent={
          !isLoading ? <EmptyState message={t('transactions.empty')} /> : null
        }
        contentContainerStyle={styles.listContent}
      />
      {Platform.OS === 'android' && (
        <FloatingActionButton
          icon="plus"
          onPress={() => router.push('/transactions/new')}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  listContent: {
    paddingVertical: spacing.sm,
  },
  headerButton: {
    color: colors.primary,
    fontSize: 16,
    fontWeight: '600',
  },
});
```

### Key Points

- Screen is a **default export** inside `app/` (expo-router convention)
- `Stack.Screen options` sets the navigation title via `t()` for i18n
- Platform-specific UI: iOS uses header button, Android uses FAB
- `FlashList` with `estimatedItemSize` for performant list rendering
- `ListEmptyComponent` shows empty state only when not loading
- Pull-to-refresh via `onRefresh` + `refreshing` from React Query
- All styles via `StyleSheet.create` with theme constants
- All user-facing strings via `t('key')`

---

## Pattern 2: Zustand Store

A UI-only Zustand store with selectors, actions, and reset function.

```typescript
// stores/useTransactionStore.ts
import { create } from 'zustand';

interface TransactionStoreState {
  filterCategory: string | null;
  sortOrder: 'asc' | 'desc';
  isFilterVisible: boolean;
  searchQuery: string;
  setFilterCategory: (category: string | null) => void;
  toggleSortOrder: () => void;
  setFilterVisible: (visible: boolean) => void;
  setSearchQuery: (query: string) => void;
  reset: () => void;
}

const initialState = {
  filterCategory: null,
  sortOrder: 'desc' as const,
  isFilterVisible: false,
  searchQuery: '',
};

export const useTransactionStore = create<TransactionStoreState>()((set) => ({
  ...initialState,
  setFilterCategory: (category) => set({ filterCategory: category }),
  toggleSortOrder: () =>
    set((state) => ({
      sortOrder: state.sortOrder === 'asc' ? 'desc' : 'asc',
    })),
  setFilterVisible: (visible) => set({ isFilterVisible: visible }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  reset: () => set(initialState),
}));

// Selector hooks for fine-grained subscriptions
export const useFilterCategory = () =>
  useTransactionStore((s) => s.filterCategory);
export const useSortOrder = () =>
  useTransactionStore((s) => s.sortOrder);
export const useIsFilterVisible = () =>
  useTransactionStore((s) => s.isFilterVisible);
export const useSearchQuery = () =>
  useTransactionStore((s) => s.searchQuery);
```

### Key Points

- `initialState` extracted as a constant for the `reset()` method
- Store contains **UI state only**: filters, sort order, visibility toggles
- **Never** store server data, API responses, or database records in Zustand
- Selector hooks exported for fine-grained subscriptions (avoids unnecessary re-renders)
- `reset()` method required for testing (reset store between tests)
- `interface` used for store state type (Zustand convention)
- Actions are simple `set()` calls; complex logic goes in services

---

## Pattern 3: React Query Hook

Query and mutation hooks using the centralised query key factory.

```typescript
// queries/useTransactions.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getTransactions,
  getTransactionById,
  createTransaction,
  updateTransaction,
  deleteTransaction,
} from '@/db/queries/transactions';
import { queryKeys } from './queryKeys';

export function useTransactions() {
  return useQuery({
    queryKey: queryKeys.transactions.all,
    queryFn: getTransactions,
    staleTime: 5 * 60 * 1000,
  });
}

export function useTransaction(id: string) {
  return useQuery({
    queryKey: queryKeys.transactions.detail(id),
    queryFn: () => getTransactionById(id),
    enabled: !!id,
  });
}

export function useCreateTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.transactions.all });
    },
  });
}

export function useUpdateTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateTransaction,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.transactions.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.transactions.detail(variables.id),
      });
    },
  });
}

export function useDeleteTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.transactions.all });
    },
  });
}
```

### Query Key Factory

```typescript
// queries/queryKeys.ts
export const queryKeys = {
  transactions: {
    all: ['transactions'] as const,
    lists: () => [...queryKeys.transactions.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.transactions.lists(), filters] as const,
    details: () => [...queryKeys.transactions.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.transactions.details(), id] as const,
  },
};
```

### Key Points

- One file per entity: `queries/use<Entity>.ts`
- Query key factory in `queries/queryKeys.ts` for consistent cache management
- `useQuery` for reads with appropriate `staleTime`
- `useMutation` for writes with `onSuccess` invalidation
- `enabled: !!id` to prevent queries with empty IDs
- Mutations invalidate both the list and detail queries on success
- `queryFn` calls Drizzle query functions (never inline DB calls)

---

## Pattern 4: Drizzle ORM Query Module

Typed CRUD functions for a database entity, called from React Query hooks.

```typescript
// db/queries/transactions.ts
import { eq, desc, and, like, between } from 'drizzle-orm';
import { db } from '../client';
import { transactions, type NewTransaction } from '../schema';

export async function getTransactions() {
  return db.select().from(transactions).orderBy(desc(transactions.createdAt));
}

export async function getTransactionById(id: string) {
  const result = await db
    .select()
    .from(transactions)
    .where(eq(transactions.id, id))
    .limit(1);
  return result[0] ?? null;
}

export async function getTransactionsByCategory(category: string) {
  return db
    .select()
    .from(transactions)
    .where(eq(transactions.category, category))
    .orderBy(desc(transactions.createdAt));
}

export async function createTransaction(data: NewTransaction) {
  return db.insert(transactions).values(data).returning();
}

export async function updateTransaction(data: { id: string } & Partial<NewTransaction>) {
  const { id, ...values } = data;
  return db
    .update(transactions)
    .set({ ...values, updatedAt: new Date() })
    .where(eq(transactions.id, id))
    .returning();
}

export async function deleteTransaction(id: string) {
  return db.delete(transactions).where(eq(transactions.id, id));
}
```

### Key Points

- All database operations live in `db/queries/<entity>.ts`
- Functions are plain `async` -- not hooks, not classes
- Called from React Query hooks (`queryFn` / `mutationFn`), never from components
- Use Drizzle query builder (`eq`, `desc`, `and`, `like`, `between`)
- `returning()` on insert/update to get the created/updated record
- Single-record lookups return `result[0] ?? null` (not `result[0]!`)
- Type imports from schema: `type NewTransaction` for insert payloads

---

## Pattern 5: Component with StyleSheet

A reusable component using theme constants, spacing scale, and platform shadows.

```typescript
// components/ui/TransactionCard.tsx
import { View, Text, Pressable, StyleSheet, Platform } from 'react-native';
import { Image } from 'expo-image';
import { useTranslation } from 'react-i18next';
import { colors, spacing, typography, borderRadius, shadows } from '@/constants';

interface TransactionCardProps {
  transaction: Transaction;
  onPress?: () => void;
}

export const TransactionCard = React.memo(function TransactionCard({
  transaction,
  onPress,
}: TransactionCardProps) {
  const { t } = useTranslation();

  return (
    <Pressable style={styles.container} onPress={onPress}>
      <View style={styles.row}>
        <Image
          source={{ uri: transaction.iconUrl }}
          style={styles.icon}
          contentFit="cover"
        />
        <View style={styles.content}>
          <Text style={styles.title} numberOfLines={1}>
            {transaction.description}
          </Text>
          <Text style={styles.category}>
            {t(`categories.${transaction.category}`)}
          </Text>
        </View>
        <Text
          style={[
            styles.amount,
            transaction.amount < 0 ? styles.amountNegative : styles.amountPositive,
          ]}
        >
          {formatCurrency(transaction.amount)}
        </Text>
      </View>
    </Pressable>
  );
});

const styles = StyleSheet.create({
  container: {
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    marginHorizontal: spacing.md,
    marginVertical: spacing.xs,
    ...shadows.sm,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  icon: {
    width: 40,
    height: 40,
    borderRadius: borderRadius.full,
    marginRight: spacing.sm,
  },
  content: {
    flex: 1,
  },
  title: {
    ...typography.body,
    color: colors.text,
  },
  category: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  amount: {
    ...typography.heading3,
  },
  amountPositive: {
    color: colors.success,
  },
  amountNegative: {
    color: colors.error,
  },
});
```

### Key Points

- `React.memo()` wraps list item components for performance
- All styles via `StyleSheet.create` (never inline objects)
- Theme constants imported from `@/constants` (colors, spacing, typography, borderRadius, shadows)
- Spacing uses the scale: `xs=4, sm=8, md=16, lg=24, xl=32, xxl=48`
- Platform shadows via `shadows` constants (differ for iOS vs Android)
- `expo-image` used instead of `<Image>` from react-native
- All user-facing strings use `t()` for i18n
- `numberOfLines` for text truncation

---

## Pattern 6: Form Screen

A modal screen with form inputs, keyboard handling, validation, and `router.back()` on success.

```typescript
// app/(modals)/transaction-form.tsx
import { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  KeyboardAvoidingView,
  Pressable,
  Platform,
  StyleSheet,
  Alert,
} from 'react-native';
import { Stack, router, useLocalSearchParams } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { useCreateTransaction, useUpdateTransaction, useTransaction } from '@/queries/useTransactions';
import { TextInput } from '@/components/ui/TextInput';
import { Select } from '@/components/ui/Select';
import { colors, spacing } from '@/constants';

export default function TransactionFormScreen() {
  const { t } = useTranslation();
  const { id } = useLocalSearchParams<{ id?: string }>();
  const isEditing = !!id;

  const { data: existing } = useTransaction(id ?? '');
  const createMutation = useCreateTransaction();
  const updateMutation = useUpdateTransaction();

  const [description, setDescription] = useState(existing?.description ?? '');
  const [amount, setAmount] = useState(existing?.amount?.toString() ?? '');
  const [category, setCategory] = useState(existing?.category ?? '');

  const isValid = description.trim().length > 0 && amount.trim().length > 0;
  const isSaving = createMutation.isPending || updateMutation.isPending;

  const handleSave = async () => {
    if (!isValid) return;

    try {
      const payload = {
        description: description.trim(),
        amount: parseFloat(amount),
        category,
      };

      if (isEditing && id) {
        await updateMutation.mutateAsync({ id, ...payload });
      } else {
        await createMutation.mutateAsync(payload);
      }
      router.back();
    } catch {
      Alert.alert(t('common.error'), t('transactions.saveFailed'));
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <Stack.Screen
        options={{
          title: isEditing ? t('transactions.edit') : t('transactions.create'),
          headerRight: () => (
            <Pressable onPress={handleSave} disabled={!isValid || isSaving}>
              <Text
                style={[
                  styles.saveButton,
                  (!isValid || isSaving) && styles.saveButtonDisabled,
                ]}
              >
                {t('common.save')}
              </Text>
            </Pressable>
          ),
        }}
      />
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <TextInput
          label={t('transactions.description')}
          value={description}
          onChangeText={setDescription}
          placeholder={t('transactions.descriptionPlaceholder')}
          autoFocus
        />
        <TextInput
          label={t('transactions.amount')}
          value={amount}
          onChangeText={setAmount}
          placeholder="0.00"
          keyboardType="decimal-pad"
        />
        <Select
          label={t('transactions.category')}
          value={category}
          onValueChange={setCategory}
          options={categoryOptions}
        />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    padding: spacing.md,
    gap: spacing.md,
  },
  saveButton: {
    color: colors.primary,
    fontSize: 16,
    fontWeight: '600',
  },
  saveButtonDisabled: {
    opacity: 0.4,
  },
});
```

### Key Points

- `KeyboardAvoidingView` with platform-specific `behavior` (`'padding'` for iOS, `'height'` for Android)
- `keyboardShouldPersistTaps="handled"` on ScrollView to prevent keyboard dismiss issues
- `useLocalSearchParams` for route parameters (edit mode detection)
- React Query mutations for create/update operations
- `Alert.alert()` for error display (native alert pattern)
- `router.back()` on successful save (dismisses modal)
- Validation state derived from form values (`isValid`)
- Save button disabled while saving (`isSaving` from mutation `isPending`)
- All strings via `t()` for i18n

---

## Pattern 7: Navigation Layout

Root layout with providers, tab layout with icons, and route groups.

### Root Layout

```typescript
// app/_layout.tsx
import { Stack } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nextProvider } from 'react-i18next';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import i18n from '@/locales/i18n';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 2,
    },
  },
});

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={queryClient}>
          <Stack>
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
            <Stack.Screen
              name="(modals)"
              options={{ presentation: 'modal', headerShown: false }}
            />
          </Stack>
        </QueryClientProvider>
      </I18nextProvider>
    </SafeAreaProvider>
  );
}
```

### Tab Layout

```typescript
// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '@/constants';

export default function TabLayout() {
  const { t } = useTranslation();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: t('tabs.home'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="transactions"
        options={{
          title: t('tabs.transactions'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="list-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: t('tabs.settings'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="settings-outline" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
```

### Key Points

- Root layout wraps the app with providers: `SafeAreaProvider`, `I18nextProvider`, `QueryClientProvider`
- `QueryClient` configured with default `staleTime` and `retry`
- Route groups: `(tabs)` for tab navigation, `(modals)` for modal presentation
- Tab layout uses `expo-router` `Tabs` component with icon configuration
- Tab labels use `t()` for i18n
- Theme colors from constants for tab bar tint

---

## Quick Reference

| I need to... | Use this pattern |
|---|---|
| Display a list of data | Pattern 1: Screen with Data Loading |
| Track UI state (filters, modals) | Pattern 2: Zustand Store |
| Fetch or mutate data | Pattern 3: React Query Hook |
| Read/write to database | Pattern 4: Drizzle ORM Query Module |
| Build a reusable UI component | Pattern 5: Component with StyleSheet |
| Build a create/edit form | Pattern 6: Form Screen |
| Set up navigation structure | Pattern 7: Navigation Layout |
