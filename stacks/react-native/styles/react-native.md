# React Native Style Guide

Style conventions for all React Native + Expo code in this mobile application.
These rules are enforced by ESLint, TypeScript strict mode, and Prettier. All
agents must follow these conventions when generating or modifying code.

---

## 1. StyleSheet.create Rules

**Always** use `StyleSheet.create()` for all styles. Never use inline style objects.

```typescript
// CORRECT
const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: spacing.md,
    backgroundColor: colors.background,
  },
});

<View style={styles.container} />

// CORRECT - combining styles
<View style={[styles.container, styles.centered]} />

// CORRECT - conditional styles
<Text style={[styles.label, isActive && styles.labelActive]} />

// WRONG - inline style object
<View style={{ flex: 1, padding: 16, backgroundColor: '#fff' }} />

// WRONG - computed object outside StyleSheet
const customStyle = { padding: 16 };
<View style={customStyle} />
```

Define styles at the bottom of the file, after the component:

```typescript
export function MyComponent() {
  return <View style={styles.container}>...</View>;
}

const styles = StyleSheet.create({
  container: { ... },
});
```

---

## 2. Theme Constants

Import all visual values from `@/constants`. **Never hardcode** colours, fonts,
or border radii.

```typescript
// CORRECT
import { colors, spacing, typography, borderRadius, shadows } from '@/constants';

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    ...shadows.sm,
  },
  title: {
    ...typography.heading3,
    color: colors.text,
  },
});

// WRONG - hardcoded values
const styles = StyleSheet.create({
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
  },
});
```

Available constant modules:

| Module | Purpose | Example |
|---|---|---|
| `colors` | Colour palette | `colors.primary`, `colors.text`, `colors.surface` |
| `spacing` | Spacing scale | `spacing.xs`, `spacing.md`, `spacing.xl` |
| `typography` | Font presets | `typography.body`, `typography.heading3` |
| `borderRadius` | Border radius scale | `borderRadius.sm`, `borderRadius.md` |
| `shadows` | Platform shadows | `shadows.sm`, `shadows.md` |
| `layout` | Screen dimensions | `layout.screenWidth`, `layout.safeAreaTop` |

---

## 3. Spacing Scale

Use the standard spacing scale for all padding, margin, and gap values:

| Token | Value | Use for |
|---|---|---|
| `spacing.xs` | 4 | Tight spacing, icon gaps |
| `spacing.sm` | 8 | Inner padding, list item gaps |
| `spacing.md` | 16 | Standard padding, section gaps |
| `spacing.lg` | 24 | Section separators, card padding |
| `spacing.xl` | 32 | Screen-level padding, major sections |
| `spacing.xxl` | 48 | Hero areas, large separators |

```typescript
// CORRECT
padding: spacing.md,
marginBottom: spacing.lg,
gap: spacing.sm,

// WRONG
padding: 16,
marginBottom: 24,
gap: 8,
```

---

## 4. Platform.OS Handling

Use `Platform.OS` for platform-specific behaviour. Common differences:

| Concern | iOS | Android |
|---|---|---|
| Navigation add button | Header right button | FloatingActionButton |
| Shadows | `shadowColor/Offset/Opacity/Radius` | `elevation` |
| Status bar | Light/dark content style | Translucent status bar |
| Keyboard avoiding | `behavior="padding"` | `behavior="height"` |
| Back navigation | Swipe from left edge | Hardware back button |
| Font weight | Supports all weights | Limited weight support |

```typescript
// Platform-specific keyboard behaviour
<KeyboardAvoidingView
  behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
/>

// Platform-specific UI elements
{Platform.OS === 'ios' && (
  <HeaderButton title="Add" onPress={handleAdd} />
)}
{Platform.OS === 'android' && (
  <FloatingActionButton icon="plus" onPress={handleAdd} />
)}

// Platform-specific styles using the shadows constant
const styles = StyleSheet.create({
  card: {
    ...shadows.sm,  // Handles iOS shadows + Android elevation
  },
});
```

---

## 5. FlashList Usage

Use `FlashList` for any list with more than ~20 items. Never use `ScrollView` +
`.map()` or `FlatList` for long lists.

```typescript
// CORRECT
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={items}
  renderItem={({ item }) => <ItemCard item={item} />}
  estimatedItemSize={72}
  onRefresh={refetch}
  refreshing={isRefreshing}
  ListEmptyComponent={<EmptyState message={t('items.empty')} />}
  contentContainerStyle={styles.listContent}
/>

// WRONG - ScrollView + map for dynamic data
<ScrollView>
  {items.map((item) => <ItemCard key={item.id} item={item} />)}
</ScrollView>

// WRONG - FlatList for long lists
<FlatList
  data={items}
  renderItem={({ item }) => <ItemCard item={item} />}
/>
```

Rules:
- **Always** set `estimatedItemSize` (height of a typical item in pixels)
- Extract `renderItem` into a named component -- no anonymous functions
- Use `ListEmptyComponent` for empty state (only when not loading)
- Use `onRefresh` + `refreshing` for pull-to-refresh

---

## 6. React.memo and Performance

Wrap list item components with `React.memo()`. Use `useCallback` for event
handlers passed to children. Use `useMemo` for expensive computations.

```typescript
// CORRECT - memoized list item
export const TransactionCard = React.memo(function TransactionCard({
  transaction,
  onPress,
}: TransactionCardProps) {
  return (
    <Pressable onPress={onPress}>
      <Text>{transaction.description}</Text>
    </Pressable>
  );
});

// CORRECT - stable callback reference
const handlePress = useCallback((id: string) => {
  router.push(`/transactions/${id}`);
}, []);

// CORRECT - memoized computation
const sortedItems = useMemo(
  () => items?.slice().sort((a, b) => compareByDate(a, b)),
  [items]
);

// WRONG - anonymous function in renderItem
<FlashList
  renderItem={({ item }) => (
    <Pressable onPress={() => handlePress(item.id)}>
      <Text>{item.name}</Text>
    </Pressable>
  )}
/>
```

When to use:
- `React.memo`: All list item components, expensive pure components
- `useCallback`: Event handlers passed to memoized children or list items
- `useMemo`: Sorted/filtered/computed data derived from state or props

---

## 7. expo-image

Use `expo-image` instead of `<Image>` from `react-native` for all image display:

```typescript
// CORRECT
import { Image } from 'expo-image';

<Image
  source={{ uri: user.avatarUrl }}
  style={styles.avatar}
  contentFit="cover"
  placeholder={blurhash}
  transition={200}
/>

// WRONG
import { Image } from 'react-native';

<Image source={{ uri: user.avatarUrl }} style={styles.avatar} />
```

`expo-image` provides: caching, blurhash placeholders, transitions, and better
performance than the built-in `Image` component.

---

## 8. i18n Requirements

All user-facing strings **must** use the `t()` function from `react-i18next`.
Never hardcode UI text.

```typescript
// CORRECT
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  return (
    <>
      <Text>{t('transactions.title')}</Text>
      <Text>{t('transactions.count', { count: items.length })}</Text>
      <Button title={t('common.save')} />
    </>
  );
}

// WRONG - hardcoded string
<Text>Transactions</Text>
<Button title="Save" />
```

Rules:
- Translation keys use **dot notation**: `t('feature.section.label')`
- Add new keys to `locales/en.json` (and other locale files)
- Use interpolation for dynamic values: `t('key', { count: 5 })`
- Never concatenate translated strings -- use interpolation instead

```json
{
  "transactions": {
    "title": "Transactions",
    "count": "{{count}} transactions",
    "empty": "No transactions yet",
    "saveFailed": "Failed to save transaction"
  },
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "error": "Error",
    "add": "Add"
  }
}
```

---

## 9. Import Conventions

Use the `@/` alias mapped to the project root. Group imports in five sections:

```typescript
// 1. React / React Native
import { useState, useCallback, useMemo } from 'react';
import { View, Text, StyleSheet, Platform, Pressable } from 'react-native';

// 2. Expo / expo-router
import { Stack, router, useLocalSearchParams } from 'expo-router';
import { Image } from 'expo-image';

// 3. Third-party
import { FlashList } from '@shopify/flash-list';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';

// 4. Internal (@/ alias)
import { useTransactions } from '@/queries/useTransactions';
import { TransactionCard } from '@/components/lists/TransactionCard';
import { colors, spacing } from '@/constants';

// 5. Relative (co-located files only)
import { formatAmount } from './utils';
```

---

## 10. Naming Conventions

| Entity | Convention | Example |
|---|---|---|
| Screen file | kebab-case or index | `transactions.tsx`, `[id].tsx` |
| Component | PascalCase | `TransactionCard`, `EmptyState` |
| Component file | PascalCase.tsx | `TransactionCard.tsx` |
| Zustand store | `use` + PascalCase + `Store` | `useTransactionStore` |
| Store file | camelCase.ts | `useTransactionStore.ts` |
| React Query hook | `use` + PascalCase | `useTransactions`, `useCreateTransaction` |
| Query hook file | camelCase.ts | `useTransactions.ts` |
| Drizzle query file | camelCase.ts | `transactions.ts` |
| Constants file | camelCase.ts | `colors.ts`, `spacing.ts` |
| Test file | Component + `.test.tsx` | `TransactionCard.test.tsx` |
| Translation key | dot.notation | `transactions.title` |
| Route group | `(groupName)` | `(tabs)`, `(modals)`, `(auth)` |

---

## 11. TypeScript Strict Mode

TypeScript strict mode is enabled. Follow these rules:

```typescript
// No `any` -- use `unknown` with type guards
// CORRECT
function handleError(error: unknown): string {
  if (error instanceof Error) return error.message;
  return 'An unknown error occurred';
}

// WRONG
function handleError(error: any): string {
  return error.message;
}

// No unsafe `as` casts -- narrow types instead
// CORRECT
const result = await db.select().from(items).where(eq(items.id, id)).limit(1);
const item = result[0] ?? null;

// WRONG
const item = result[0] as Item;

// Use optional chaining and nullish coalescing
// CORRECT
const name = user?.profile?.name ?? 'Unknown';

// WRONG
const name = user!.profile!.name;
```

Rules:
- No `any` types -- use `unknown` and narrow
- No unsafe `as` casts -- use type guards and narrowing
- No `!` non-null assertions -- use optional chaining and nullish coalescing
- Export props interfaces for reuse
- Use discriminated unions for variant types

---

## 12. Error Handling

Handle three states for every data operation: **loading**, **error**, and **success**.

```typescript
// Using React Query states
const { data, isLoading, error } = useTransactions();

if (isLoading) return <LoadingScreen />;
if (error) return <ErrorScreen message={t('transactions.loadFailed')} />;

// Mutation errors with Alert.alert
const createMutation = useCreateTransaction();

const handleSave = async () => {
  try {
    await createMutation.mutateAsync(payload);
    router.back();
  } catch {
    Alert.alert(t('common.error'), t('transactions.saveFailed'));
  }
};
```

Rules:
- Use React Query `isLoading` and `error` states for query operations
- Use `Alert.alert()` for user-facing error messages in mutations
- Always wrap `mutateAsync` in try/catch
- Show empty state when data is loaded but empty (`ListEmptyComponent`)
- Never ignore errors silently

---

## 13. Safe Area and Keyboard

Use `SafeAreaView` or `useSafeAreaInsets` for notch and Dynamic Island handling.
Use `KeyboardAvoidingView` for form screens.

```typescript
// Safe area handling
import { SafeAreaView } from 'react-native-safe-area-context';
// or
import { useSafeAreaInsets } from 'react-native-safe-area-context';

function MyScreen() {
  const insets = useSafeAreaInsets();
  return (
    <View style={{ paddingTop: insets.top, paddingBottom: insets.bottom }}>
      ...
    </View>
  );
}

// Keyboard handling for forms
<KeyboardAvoidingView
  style={styles.container}
  behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
>
  <ScrollView keyboardShouldPersistTaps="handled">
    {/* form inputs */}
  </ScrollView>
</KeyboardAvoidingView>
```

Rules:
- Use `react-native-safe-area-context` (not the deprecated `SafeAreaView` from RN)
- Use `useSafeAreaInsets()` for fine-grained control
- Wrap form screens in `KeyboardAvoidingView`
- Set `behavior` per platform: `'padding'` for iOS, `'height'` for Android
- Set `keyboardShouldPersistTaps="handled"` on `ScrollView` inside keyboard views

---

## 14. ESLint and TypeScript Enforcement

These rules are enforced by ESLint and TypeScript. Run before every commit:

```bash
# TypeScript check
npx tsc --noEmit

# Linting
npm run lint

# Formatting
npx prettier --write .
```

Key ESLint rules:
- `@typescript-eslint/no-explicit-any` -- disallow `any`
- `@typescript-eslint/no-non-null-assertion` -- disallow `!` operator
- `react-hooks/rules-of-hooks` -- enforce rules of hooks
- `react-hooks/exhaustive-deps` -- enforce correct dependency arrays
- `react-native/no-inline-styles` -- disallow inline style objects
- `react-native/no-color-literals` -- disallow hardcoded colours in styles

All three commands must pass with zero errors before code is considered complete.
