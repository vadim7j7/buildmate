---
name: new-container
description: Generate a new container component with data fetching, state management, and event handlers
---

# /new-container

## What This Does

Creates a new container component that handles data fetching, state management,
and event handling. Containers are the bridge between pages and presentational
components, following the Page -> Container -> Component pattern.

## Usage

```
/new-container ProjectList
/new-container ProjectDetail
/new-container CreateProject
/new-container EditProject
```

## How It Works

### 1. Determine Container Type

Based on the name, infer the purpose:

| Name Pattern | Container Type |
|---|---|
| `*List` | List container: fetches array, renders list component |
| `*Detail` | Detail container: fetches single item by ID |
| `Create*` | Create form container: handles form submission |
| `Edit*` | Edit form container: fetches item + handles update |

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` for conventions
- `skills/new-container/references/container-examples.md` for examples
- Existing containers in `src/containers/` for project-specific patterns
- Matching service in `src/services/` for API functions

### 3. Generate Files

#### Container: `src/containers/<Name>Container.tsx`

All containers are `'use client'` components that:
- Fetch data via service functions
- Manage loading / error / success states
- Handle events (create, update, delete)
- Pass data to presentational components

### 4. Verify

Run `npx tsc --noEmit` to verify the container compiles.

## Rules

- All containers use `'use client'` directive
- Data fetching uses `useEffect` with IIFE async pattern
- Error handling with try/catch and `showNotification`
- Loading states with Mantine's `LoadingOverlay` or `Loader`
- Error states with Mantine's `Alert`
- Empty states handled explicitly
- Use `type` for props (not `interface`)
- Named export with `Container` suffix

## Output

```
Created:
  src/containers/<Name>Container.tsx       -- Container implementation
  src/containers/<Name>Container.test.tsx  -- Unit tests

Verified:
  npx tsc --noEmit  -- PASS
```
