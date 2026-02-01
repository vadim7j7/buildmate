---
name: new-screen
description: Generate a new expo-router screen with proper patterns
---

# /new-screen -- Generate an Expo Router Screen

## What This Does

Generates a new screen file using expo-router conventions. Creates the screen
component with proper data loading, navigation, styling, i18n, and
platform-specific UI patterns.

## Usage

```
/new-screen Settings                   # Tab screen at app/(tabs)/settings.tsx
/new-screen TransactionDetail          # Detail screen at app/(tabs)/transactions/[id].tsx
/new-screen AddTransaction --modal     # Modal screen at app/(modals)/add-transaction.tsx
/new-screen Login --auth               # Auth screen at app/(auth)/login.tsx
/new-screen BudgetList --type=list     # List screen with FlashList
/new-screen BudgetForm --type=form     # Form screen with KeyboardAvoidingView
/new-screen BudgetDetail --type=detail # Detail screen with ScrollView
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name`   | Yes      | Screen name in PascalCase (e.g., `Settings`, `TransactionDetail`) |
| `--modal` | No | Place in `app/(modals)/` instead of `app/(tabs)/` |
| `--auth` | No | Place in `app/(auth)/` instead of `app/(tabs)/` |
| `--type` | No | Screen type: `list`, `form`, or `detail`. Default: `list` |

## How It Works

### 1. Determine Screen Location

Based on the arguments:
- Default: `app/(tabs)/<kebab-name>.tsx`
- `--modal`: `app/(modals)/<kebab-name>.tsx`
- `--auth`: `app/(auth)/<kebab-name>.tsx`

Convert PascalCase to kebab-case for the filename:
- `TransactionDetail` -> `transaction-detail.tsx`
- `AddTransaction` -> `add-transaction.tsx`

If the screen needs a dynamic route parameter (detail screens), use `[id].tsx`:
- `TransactionDetail` -> `app/(tabs)/transactions/[id].tsx`

### 2. Generate the Screen File

Use the appropriate template based on `--type`:

- **list**: FlashList with data loading, pull-to-refresh, empty state,
  platform-specific add action (iOS header button, Android FAB)
- **form**: KeyboardAvoidingView, ScrollView, form inputs, header save button,
  validation, mutation with error handling
- **detail**: ScrollView with sections, data loading, loading/error states

See `references/screen-examples.md` for complete templates.

### 3. Generate Supporting Files

Based on the screen's needs, also create:
- React Query hook in `queries/use<Entity>.ts` (if it doesn't exist)
- Drizzle query functions in `db/queries/<entity>.ts` (if it doesn't exist)
- i18n keys in `locales/en.json` (append to existing file)

### 4. Verify

Run TypeScript check after generating:

```bash
npx tsc --noEmit
```

## Screen Type Templates

### List Screen

Key features:
- FlashList with `estimatedItemSize`
- React Query hook for data loading
- Pull-to-refresh via `onRefresh`
- Empty state component
- Platform-specific primary action (iOS header button, Android FAB)
- Loading and error states

### Form Screen

Key features:
- KeyboardAvoidingView with platform-specific `behavior`
- ScrollView with `keyboardShouldPersistTaps="handled"`
- Header save button (disabled while invalid or saving)
- Form state in component (or Zustand for drafts)
- useMutation for submission
- Validation before save
- Error handling with Alert

### Detail Screen

Key features:
- ScrollView with content sections
- useLocalSearchParams for ID parameter
- React Query hook for single-item loading
- Loading screen while fetching
- Error screen for not-found
- Section components for content organisation

## Naming Conventions

| Input | File | Component |
|-------|------|-----------|
| `Settings` | `settings.tsx` | `SettingsScreen` |
| `TransactionList` | `transaction-list.tsx` | `TransactionListScreen` |
| `AddBudget` | `add-budget.tsx` | `AddBudgetScreen` |
| `BudgetDetail` | `budgets/[id].tsx` | `BudgetDetailScreen` |
