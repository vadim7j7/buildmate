---
name: new-store
description: Generate a new Zustand store for UI state management
---

# /new-store -- Generate a Zustand Store

## What This Does

Generates a new Zustand store following project conventions. Stores hold
**UI state ONLY** -- never server data or database records.

## Usage

```
/new-store budget            # stores/useBudgetStore.ts
/new-store transactionFilter # stores/useTransactionFilterStore.ts
/new-store app               # stores/useAppStore.ts
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name`   | Yes      | Store name in camelCase (e.g., `budget`, `transactionFilter`) |

## How It Works

### 1. Determine File Location

Place the store at:
```
stores/use<PascalCaseName>Store.ts
```

### 2. Generate the Store

Create the store with:
- TypeScript interface for state + actions
- `initialState` object (extracted for reset)
- `create<State>()((set) => ({...}))` pattern
- `reset()` action that restores initial state
- Exported selector hooks for fine-grained subscriptions

See `references/store-examples.md` for templates.

### 3. Generate Test File

Create a test at:
```
__tests__/stores/use<PascalCaseName>Store.test.ts
```

With tests for:
- Initial state values
- Each action/setter
- Reset to initial state
- Each test resets the store in `beforeEach`

### 4. Verify

```bash
npx tsc --noEmit
```

## CRITICAL RULES

### UI State ONLY

A Zustand store MUST only contain transient UI state. Ask yourself: "Does this
data come from an API or database?" If yes, it belongs in React Query, not Zustand.

**Acceptable state:**
- Filter selections, sort order, search query
- Modal visibility, bottom sheet state
- Form drafts (before submission)
- Selected items (multi-select UI)
- Tab index, accordion open/closed
- Theme preference, locale selection
- Onboarding progress

**NEVER in Zustand:**
- User profile data (from API)
- Transaction list (from database)
- Budget amounts (from database)
- Any cached server response

### Required Patterns

1. Extract `initialState` for the `reset()` action
2. Always include a `reset()` action
3. Export selector hooks (not the whole store)
4. Use `as const` for literal types in initial state
