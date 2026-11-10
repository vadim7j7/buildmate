---
name: new-composable
description: Generate a Nuxt 4 composable with reactive state and API integration
---

# /new-composable

## What This Does

Generates a Nuxt 4 composable in `app/composables/` with SSR-safe data loading
(`useFetch` / `useAsyncData` at setup time), imperative actions (`$fetch`), and a test file.

## Usage

```
/new-composable projects     # Creates app/composables/useProjects.ts
/new-composable auth          # Creates app/composables/useAuth.ts
/new-composable notifications # Creates app/composables/useNotifications.ts
```

## How It Works

1. **Read reference patterns** from `patterns/nuxt-patterns.md` and `styles/typescript.md`
2. **Generate composable**:
   - reads via `useFetch` / `useAsyncData` called synchronously in the composable
     (which itself is called from `<script setup>`), exposing `data`, `status`, `error`, `refresh`
   - mutations and later loads via `$fetch` inside returned functions — never `useFetch`
     inside a function that runs after setup
3. **Generate test file** with Vitest in the `nuxt` environment (`@nuxt/test-utils`,
   `registerEndpoint` to fake the API, `mockNuxtImport` for other composables)
4. **Run quality checks**: `npx nuxi typecheck && npm run lint && npx vitest run`

## Generated Files

```
app/composables/use<Name>.ts
tests/composables/use<Name>.nuxt.test.ts
```
