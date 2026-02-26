---
name: new-composable
description: Generate a Nuxt 3 composable with reactive state and API integration
---

# /new-composable

## What This Does

Generates a Nuxt 3 composable function with reactive state management, API integration,
loading/error handling, and a test file.

## Usage

```
/new-composable projects     # Creates composables/useProjects.ts
/new-composable auth          # Creates composables/useAuth.ts
/new-composable notifications # Creates composables/useNotifications.ts
```

## How It Works

1. **Read reference patterns** from `patterns/nuxt-patterns.md` and `styles/typescript.md`
2. **Generate composable** with reactive refs, methods, and error handling
3. **Generate test file** with Vitest
4. **Run quality checks**: `npx tsc --noEmit && npm run lint && npx vitest run`

## Generated Files

```
composables/use<Name>.ts
tests/composables/use<Name>.test.ts
```
