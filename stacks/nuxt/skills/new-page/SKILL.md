---
name: new-page
description: Generate a Nuxt 4 page with data fetching and error handling
---

# /new-page

## What This Does

Generates a Nuxt 4 page component in `app/pages/` with SSR-safe data fetching,
loading states, and error handling.

## Usage

```
/new-page projects          # Creates app/pages/projects/index.vue
/new-page projects/[id]     # Creates app/pages/projects/[id].vue (dynamic route)
/new-page settings           # Creates app/pages/settings.vue
```

## How It Works

1. **Read reference patterns** from `.claude/patterns/nuxt-patterns.md` and `.claude/styles/typescript.md`
2. **Generate page component** with `<script setup lang="ts">`, `await useFetch(...)` at
   setup time, and loading/error states from `status` (`'pending' | 'success' | 'error'`)
   and `error` — not the removed `pending` flag
3. **Generate server route** if the API endpoint doesn't exist (`/new-server-route`)
4. **Generate a component test** with `mountSuspended` from `@nuxt/test-utils/runtime`
5. **Run quality checks**: `npx nuxi typecheck && npm run lint && npx vitest run`

If the project keeps pages at the root (`pages/`, Nuxt 3 layout), follow that instead.

## Generated Files

```
app/pages/<path>.vue
tests/pages/<path>.nuxt.test.ts
server/api/<resource>/... (if needed)
```
