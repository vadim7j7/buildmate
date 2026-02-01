# React Native + Expo Agent System

This project uses a multi-agent architecture powered by Claude Code, specialised for
React Native + Expo mobile applications. A single main agent orchestrates work by
delegating to specialised sub-agents through the **Task** tool. Sub-agents never
spawn their own sub-agents; only the main agent delegates.

## Quick Start

Say **"Use PM: [task description]"** in any conversation to trigger the full
orchestration pipeline. The PM agent will break the task down, create a feature file,
and drive the pipeline to completion.

## Technology Stack

| Technology       | Version / Notes                                              |
|------------------|--------------------------------------------------------------|
| Expo SDK         | 54                                                           |
| React Native     | 0.81+                                                        |
| TypeScript       | Strict mode enabled                                          |
| Navigation       | expo-router v4                                               |
| UI State         | Zustand (UI state ONLY -- loading, modals, form drafts)      |
| Server State     | React Query (TanStack Query v5)                              |
| Database         | Drizzle ORM (local SQLite via expo-sqlite)                   |
| Lists            | FlashList (NOT ScrollView + map, NOT FlatList for long lists)|
| i18n             | i18next + react-i18next                                      |
| Testing          | Jest + React Native Testing Library                          |
| Linting          | ESLint + Prettier                                            |

## Project Structure

```
app/
  (tabs)/              # Tab-based navigation screens
  (modals)/            # Modal navigation screens
  (auth)/              # Authentication flow screens
  _layout.tsx          # Root layout (providers, themes)
  +not-found.tsx       # 404 screen
components/
  ui/                  # Reusable UI primitives (Button, Input, Card, etc.)
  forms/               # Form-specific components
  lists/               # List item components
  layout/              # Layout wrappers (SafeArea, KeyboardAvoiding, etc.)
stores/
  useAppStore.ts       # Global app UI state (theme, locale, onboarding)
  use<Feature>Store.ts # Feature-specific UI state
queries/
  use<Entity>.ts       # React Query hooks per entity
  queryKeys.ts         # Centralised query key factory
db/
  schema.ts            # Drizzle ORM schema definitions
  migrations/          # Drizzle migration files
  queries/
    <entity>.ts        # Drizzle query functions per entity
  client.ts            # Database client initialisation
services/
  api/
    client.ts          # HTTP client (axios / fetch wrapper)
    <entity>.ts        # API service functions per entity
hooks/
  useDebounce.ts       # Custom hooks
  usePlatform.ts
  useKeyboard.ts
constants/
  colors.ts            # Theme colour palette
  spacing.ts           # Spacing scale (4, 8, 12, 16, 20, 24, 32, 48)
  typography.ts        # Font families, sizes, weights
  borderRadius.ts      # Border radius scale
  shadows.ts           # Platform-specific shadow definitions
  layout.ts            # Screen dimensions, safe area insets
locales/
  en.json              # English translations
  <lang>.json          # Additional language files
assets/
  images/              # Static images
  fonts/               # Custom fonts
__tests__/
  components/          # Component tests
  screens/             # Screen tests
  stores/              # Store tests
  queries/             # Query hook tests
  db/                  # Database query tests
```

## Key Commands

| Command                          | Purpose                              |
|----------------------------------|--------------------------------------|
| `npx expo start`                 | Start the Expo dev server            |
| `npx expo start --ios`           | Start with iOS simulator             |
| `npx expo start --android`       | Start with Android emulator          |
| `npx tsc --noEmit`               | TypeScript type check (no output)    |
| `npm run lint`                   | Run ESLint on all source files       |
| `npm test`                       | Run Jest test suite                  |
| `npx jest --watch`               | Run Jest in watch mode               |
| `npx jest path/to/test`          | Run a specific test file             |
| `npx expo install <package>`     | Install Expo-compatible package      |
| `npx prettier --write .`         | Format all files with Prettier       |

## Agent Pipeline

Every non-trivial task flows through the following stages:

```
Plan --> Implement --> Test --> Review --> Eval
```

| Stage      | Agent                | Purpose                                    |
|------------|----------------------|--------------------------------------------|
| Plan       | PM (orchestrator)    | Break task into sub-tasks, create feature  |
| Implement  | mobile-developer     | Write production React Native code         |
| Test       | mobile-tester        | Write and run Jest + RNTL tests            |
| Review     | mobile-code-reviewer | Code review against RN conventions         |
| Eval       | eval-agent           | Score against quality rubrics              |

Testing and review may run in parallel after implementation completes.

## State Management Rules

### Zustand -- UI State ONLY

Zustand stores hold **transient UI state** that does not come from the server or
database. Examples:

- Loading indicators, modal visibility, bottom sheet state
- Form draft values (before submission)
- Selected tab index, filter selections, sort order
- Onboarding progress, theme preference

Zustand stores MUST NOT hold:
- Server data (use React Query)
- Database records (use Drizzle queries via React Query)
- Cached API responses

### React Query -- Server / Database State

All data that originates from an API or local database is managed by React Query.
This includes fetching, caching, background refetching, and optimistic updates.

### Drizzle ORM -- Database Operations

All direct database reads and writes go through Drizzle query functions in `db/queries/`.
These are called from React Query hooks (`queryFn` / `mutationFn`), never directly
from components.

## Code Patterns

### Screen Pattern (expo-router)

```typescript
// app/(tabs)/transactions.tsx
import { useLocalSearchParams, Stack } from 'expo-router';
import { FlashList } from '@shopify/flash-list';
import { useTransactions } from '@/queries/useTransactions';

export default function TransactionsScreen() {
  const { data, isLoading, refetch } = useTransactions();

  return (
    <>
      <Stack.Screen options={{ title: t('transactions.title') }} />
      <FlashList
        data={data}
        renderItem={({ item }) => <TransactionCard transaction={item} />}
        estimatedItemSize={80}
        onRefresh={refetch}
        refreshing={isLoading}
      />
    </>
  );
}
```

### Zustand Store Pattern

```typescript
// stores/useTransactionStore.ts
import { create } from 'zustand';

interface TransactionStoreState {
  filterCategory: string | null;
  sortOrder: 'asc' | 'desc';
  setFilterCategory: (category: string | null) => void;
  toggleSortOrder: () => void;
  reset: () => void;
}

const initialState = {
  filterCategory: null,
  sortOrder: 'desc' as const,
};

export const useTransactionStore = create<TransactionStoreState>()((set) => ({
  ...initialState,
  setFilterCategory: (category) => set({ filterCategory: category }),
  toggleSortOrder: () =>
    set((state) => ({
      sortOrder: state.sortOrder === 'asc' ? 'desc' : 'asc',
    })),
  reset: () => set(initialState),
}));

// Selector hooks for fine-grained subscriptions
export const useFilterCategory = () =>
  useTransactionStore((s) => s.filterCategory);
export const useSortOrder = () =>
  useTransactionStore((s) => s.sortOrder);
```

### React Query Pattern

```typescript
// queries/useTransactions.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getTransactions, createTransaction } from '@/db/queries/transactions';
import { queryKeys } from './queryKeys';

export function useTransactions() {
  return useQuery({
    queryKey: queryKeys.transactions.all,
    queryFn: getTransactions,
    staleTime: 5 * 60 * 1000,
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
```

### Drizzle Query Pattern

```typescript
// db/queries/transactions.ts
import { eq, desc } from 'drizzle-orm';
import { db } from '../client';
import { transactions } from '../schema';

export async function getTransactions() {
  return db.select().from(transactions).orderBy(desc(transactions.createdAt));
}

export async function createTransaction(data: NewTransaction) {
  return db.insert(transactions).values(data).returning();
}
```

### Component Pattern

```typescript
// components/ui/TransactionCard.tsx
import { View, Text, StyleSheet, Platform } from 'react-native';
import { colors, spacing, typography, borderRadius, shadows } from '@/constants';

interface TransactionCardProps {
  transaction: Transaction;
  onPress?: () => void;
}

export function TransactionCard({ transaction, onPress }: TransactionCardProps) {
  return (
    <Pressable style={styles.container} onPress={onPress}>
      <Text style={styles.title}>{transaction.description}</Text>
      <Text style={styles.amount}>{formatCurrency(transaction.amount)}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    ...shadows.sm,
    marginHorizontal: spacing.md,
    marginVertical: spacing.xs,
  },
  title: {
    ...typography.body,
    color: colors.text,
  },
  amount: {
    ...typography.heading3,
    color: colors.primary,
  },
});
```

### i18n Pattern

All user-facing strings use the `t()` function from i18next. Never hardcode UI text.

```typescript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  return <Text>{t('transactions.emptyState')}</Text>;
}
```

Translation files live in `locales/`:

```json
{
  "transactions": {
    "title": "Transactions",
    "emptyState": "No transactions yet",
    "addNew": "Add Transaction"
  }
}
```

## Styling Rules

- Always use `StyleSheet.create()` -- never inline style objects
- Import theme constants from `@/constants` (colors, spacing, typography, etc.)
- Use the spacing scale: `xs=4, sm=8, md=16, lg=24, xl=32, xxl=48`
- Use platform-specific shadows via the `shadows` constants
- Use `Platform.OS` checks for platform-specific UI (iOS header buttons, Android FABs)
- Use `SafeAreaView` or `useSafeAreaInsets` for notch/island handling

## Navigation Rules

- All screens are files inside `app/` using expo-router file-based routing
- Tab screens go in `app/(tabs)/`
- Modal screens go in `app/(modals)/`
- Auth screens go in `app/(auth)/`
- Use `useLocalSearchParams()` for route parameters
- Use `<Link href="/path">` or `router.push('/path')` for navigation
- Use `router.back()` for dismissing modals

## Performance Rules

- Use `FlashList` for any list with more than ~20 items
- Use `React.memo()` for list item components
- Use `useCallback` for event handlers passed to list items
- Use `useMemo` for expensive computations in render
- Optimise images with `expo-image` (not `<Image>` from react-native)
- Avoid anonymous functions in `renderItem` -- extract named components
- Use `estimatedItemSize` on FlashList for optimal performance

## Quality Gates

Before the review stage, the following gates **must** pass:

| Gate       | Command              | Requirement          |
|------------|----------------------|----------------------|
| TypeScript | `npx tsc --noEmit`   | Zero errors          |
| Lint       | `npm run lint`       | Zero errors          |
| Tests      | `npm test`           | All passing          |

If any gate fails, the implementing agent must fix the issues before proceeding.

## Feature Tracking

Features are tracked as markdown files in `.claude/context/features/`.

```bash
# Convention: YYYYMMDD-short-slug.md
touch .claude/context/features/20260201-transaction-list.md
```

## Available Slash Commands

| Command           | Description                                              |
|-------------------|----------------------------------------------------------|
| `/test`           | Run Jest tests via mobile-tester agent                   |
| `/review`         | Code review via mobile-code-reviewer agent               |
| `/platform-check` | Verify platform-specific code for iOS and Android       |
| `/new-screen`     | Generate an expo-router screen                           |
| `/new-rn-component` | Generate a React Native component                     |
| `/new-store`      | Generate a Zustand store                                 |
| `/new-query`      | Generate a React Query hook                              |
| `/new-db-query`   | Generate a Drizzle ORM query module                      |

## Delegation Rules

1. **Only the main agent delegates.** Sub-agents receive a task, execute it,
   and return results. They never call the Task tool themselves.
2. **One responsibility per agent.** Each sub-agent owns a single concern
   (implementing, testing, reviewing).
3. **Context flows forward.** Each stage writes its output to
   `.agent-pipeline/<stage>.md` so the next stage can read it.
4. **Failures stop the pipeline.** If a stage fails, the pipeline halts and
   the main agent reports the failure with actionable details.
