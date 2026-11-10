---
name: new-container
description: Generate a client "container" component — an interactive island that receives server data as props and calls Server Actions
---

# /new-container

## What This Does

Creates a small `'use client'` component (a "container", or interactive island) for
the parts of a page that need interactivity: forms, delete buttons, filters, tabs,
optimistic updates.

The app is **server-first**:

- The **page** (async Server Component) fetches the data on the server from
  `src/lib/data/` and passes it down as **props**.
- The **container** owns client state and event handlers only. It does **not** fetch
  its initial data, and has no `useEffect` loading/error states for it.
- **Mutations** go through Server Actions in `src/lib/actions/`; after
  `revalidatePath()` the page re-renders with fresh props.
- **Client-side fetching** is allowed only for data that is genuinely client-driven
  (polling, infinite scroll, search-as-you-type). Use TanStack Query for it if the
  project has `@tanstack/react-query`; otherwise a small hook. Even then, the first
  page comes from the server as `initialData`.

## Usage

```
/new-container ProjectListActions
/new-container CreateProjectForm
/new-container EditProjectForm
/new-container ProjectFilters
```

## How It Works

### 1. Determine Container Type

| Name Pattern | Container Type |
|---|---|
| `*Actions` / `*Button` | Buttons that call Server Actions (`useTransition`) |
| `Create*Form` | Form bound to a Server Action with `useActionState` |
| `Edit*Form` | Same, pre-filled from the `item` prop the page fetched |
| `*Filters` / `*Search` | Updates the URL `searchParams`; the page re-fetches on the server |
| `*Feed` / `*Live*` | Client-driven data (polling / infinite scroll) with `initialData` from the page |

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` for conventions
- `skills/new-container/references/container-examples.md` for examples
- The project's UI library style guide (in `styles/`)
- Existing client components and the Server Actions in `src/lib/actions/`

### 3. Generate Files

#### Container: `src/components/<feature>/<Name>.tsx`

Every container:
- starts with `'use client'`
- receives the data it shows as typed props (serializable: plain objects, no functions from the server except Server Actions)
- calls Server Actions for writes (`useActionState` for forms, `useTransition` for buttons)
- takes its copy from `useTranslations` (next-intl), not hardcoded strings
- stays as small as possible: keep static markup in Server Components and pass it as `children`

### 4. Verify

Run `npx tsc --noEmit` to verify the container compiles.

## Rules

- `'use client'` only on the interactive island, never on the page
- Initial data arrives as props from the server; no `useEffect` fetch for it
- Writes go through Server Actions (which authenticate, authorize and validate)
- Filters/pagination write to the URL (`useRouter` / `useSearchParams`); the server page reads `searchParams`
- Client fetching only for genuinely client-driven data (TanStack Query if present)
- Pending / error feedback from `useActionState` / `useTransition` and the UI library
- Use `type` for props (not `interface`)
- Named exports

## Output

```
Created:
  src/components/<feature>/<Name>.tsx       -- Client island
  src/components/<feature>/<Name>.test.tsx  -- Unit tests (props in, actions mocked)

Verified:
  npx tsc --noEmit  -- PASS
```
