---
name: new-query
description: Generate a React Query hook for data fetching and mutations
---

# /new-query -- Generate a React Query Hook

## What This Does

Generates a React Query hook module with `useQuery` for fetching and
`useMutation` hooks for create/update/delete operations. Follows the project's
query key factory pattern and integrates with Drizzle ORM query functions.

## Usage

```
/new-query useTransactions      # queries/useTransactions.ts
/new-query useBudgets           # queries/useBudgets.ts
/new-query useCategories        # queries/useCategories.ts
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name`   | Yes      | Hook name starting with `use` in camelCase |

## How It Works

### 1. Determine File Location

Place the hook at:
```
queries/<hookName>.ts
```

### 2. Check for Drizzle Query Functions

Look for corresponding query functions in `db/queries/`. If they do not exist,
create them or inform the user they need to be created first.

### 3. Update Query Key Factory

Add query keys for the new entity to `queries/queryKeys.ts`:

```typescript
export const queryKeys = {
  // ... existing keys
  <entity>: {
    all: ['<entity>'] as const,
    lists: () => [...queryKeys.<entity>.all, 'list'] as const,
    list: (filters: Record<string, unknown>) =>
      [...queryKeys.<entity>.lists(), filters] as const,
    details: () => [...queryKeys.<entity>.all, 'detail'] as const,
    detail: (id: string) =>
      [...queryKeys.<entity>.details(), id] as const,
  },
};
```

### 4. Generate the Hook Module

Create the module with:
- `useQuery` hook for fetching all items
- `useQuery` hook for fetching a single item by ID
- `useMutation` hooks for create, update, and delete
- Proper query invalidation on mutation success
- Appropriate `staleTime` values

See `references/query-examples.md` for templates.

### 5. Generate Test File

Create a test at:
```
__tests__/queries/<hookName>.test.ts
```

### 6. Verify

```bash
npx tsc --noEmit
```

## Query Conventions

### Query Keys

- Use the centralised `queryKeys` factory in `queries/queryKeys.ts`
- Never use inline string arrays for query keys
- Follow the `all > lists > list(filters) > details > detail(id)` hierarchy

### staleTime

Choose based on data volatility:
- Static data (categories): `30 * 60 * 1000` (30 minutes)
- Moderate data (budgets): `5 * 60 * 1000` (5 minutes)
- Frequently changing data (transactions): `2 * 60 * 1000` (2 minutes)
- Always fresh (balance): `0`

### Mutation Invalidation

Always invalidate relevant queries on mutation success:
- Create: invalidate the list query
- Update: invalidate both the list and the specific detail query
- Delete: invalidate the list query

### Error Handling

- Let React Query handle retries (default: 3)
- Components should read `isError` and `error` from the hook
- Mutations should handle errors in `onError` or at the call site
