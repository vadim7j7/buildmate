---
name: new-page
description: Generate a Nuxt 3 page with data fetching and error handling
---

# /new-page

## What This Does

Generates a Nuxt 3 page component with data fetching, loading states, and error handling.

## Usage

```
/new-page projects          # Creates pages/projects/index.vue
/new-page projects/[id]     # Creates pages/projects/[id].vue (dynamic route)
/new-page settings           # Creates pages/settings.vue
```

## How It Works

1. **Read reference patterns** from `patterns/nuxt-patterns.md` and `styles/typescript.md`
2. **Generate page component** with `<script setup lang="ts">`, `useFetch`, loading/error states
3. **Generate server route** if API endpoint doesn't exist
4. **Run quality checks**: `npx tsc --noEmit && npm run lint && npx vitest run`

## Generated Files

```
pages/<path>.vue
server/api/<resource>/... (if needed)
```
