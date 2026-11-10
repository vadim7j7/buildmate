---
name: new-rn-component
description: Generate a new React Native component with the project's styling library, theme tokens, and TypeScript props
---

# /new-rn-component -- Generate a React Native Component

## What This Does

Generates a new React Native component following project conventions: TypeScript
interface for props, the project's styling library for styles (plain `StyleSheet`,
NativeWind, Tamagui or Gluestack — see `.claude/styles/`), theme constants or tokens
for colours and spacing, and platform-specific considerations.

## Usage

```
/new-rn-component TransactionCard              # List item component
/new-rn-component BudgetProgressBar            # UI primitive
/new-rn-component FilterChip --dir=ui          # In src/components/ui/
/new-rn-component CategoryBadge --dir=lists    # In src/components/lists/
/new-rn-component LoginForm --dir=forms        # In src/components/forms/
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name`   | Yes      | Component name in PascalCase (e.g., `TransactionCard`) |
| `--dir`  | No       | Subdirectory under `src/components/`. Default: `ui` |

## How It Works

### 1. Determine File Location

Place the component file at:
```
src/components/<dir>/<ComponentName>.tsx
```

Default directory is `ui`. Common directories:
- `ui/` -- Reusable UI primitives (Button, Card, TextInput, Badge)
- `lists/` -- List item components (TransactionCard, BudgetRow)
- `forms/` -- Form-specific components (CurrencyInput, DatePicker)
- `layout/` -- Layout wrappers (Section, Divider, SafeContainer)

### 2. Generate the Component

Create the component with:
- TypeScript `interface` for props (exported)
- Functional component with destructured props
- Styles the way the project's style guide in `.claude/styles/` shows: plain StyleSheet
  → `StyleSheet.create()` + theme constants from `@/constants`; NativeWind → `className`;
  Tamagui / Gluestack → their components with style props and `$tokens`
- Platform-specific handling where relevant
- Optional `testID` prop for testing
- `React.memo` wrapping if it's a list item component

See `references/rn-component-examples.md` for templates (written with plain StyleSheet;
keep their structure and swap the styling when the project uses another library).

### 3. Generate Test File

Create a corresponding test file at:
```
__tests__/components/<dir>/<ComponentName>.test.tsx
```

With basic tests for:
- Default rendering
- Props handling
- User interactions (if interactive)

### 4. Verify

```bash
npx tsc --noEmit
```

## Component Conventions

### Props Interface

```typescript
// Always export the props interface
export interface TransactionCardProps {
  transaction: Transaction;
  onPress?: (id: string) => void;
  testID?: string;
}
```

### Styles (plain StyleSheet projects)

With NativeWind, Tamagui or Gluestack, follow `.claude/styles/<library>.md` instead.

```typescript
// Always at the bottom of the file
const styles = StyleSheet.create({
  container: {
    // Use theme constants, never hardcoded values
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
  },
});
```

### Theme Constants (plain StyleSheet projects)

Always import from `@/constants`:
```typescript
import { colors, spacing, typography, borderRadius, shadows } from '@/constants';
```

### React.memo for List Items

Components used in FlashList/FlatList `renderItem` should be wrapped:
```typescript
export const TransactionCard = React.memo(function TransactionCard(props) {
  // ...
});
```
