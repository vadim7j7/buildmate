---
name: new-middleware
description: Generate Nuxt 4 route middleware (named or global) for navigation guards
---

# /new-middleware

## What This Does

Generates **route middleware** in `app/middleware/`: code that runs before a page
renders, on the server for the first request and in the browser on later
navigations. Use it to redirect (signed-out users, missing onboarding, feature
flags) or to abort navigation.

Route middleware is **not** a security boundary: it only decides which page is
shown. Data is protected in the server route (`requireUserSession` in
`server/api/...`). For request middleware on the Nitro server (logging, headers on
every request), create `server/middleware/<name>.ts` with `defineEventHandler` instead.

## Usage

```
/new-middleware auth                 # app/middleware/auth.ts (named: pages opt in)
/new-middleware analytics --global   # app/middleware/analytics.global.ts (every route)
/new-middleware admin                # role check on top of auth
```

## How It Works

1. **Read** `.claude/patterns/nuxt-patterns.md` (Route Middleware) and existing files
   in `app/middleware/`. For auth, read `nuxt-auth.md` if installed.
2. **Generate the middleware**:

   ```ts
   // app/middleware/admin.ts
   export default defineNuxtRouteMiddleware((to) => {
     const { loggedIn, user } = useUserSession();

     if (!loggedIn.value) {
       return navigateTo({ path: '/login', query: { redirect: to.fullPath } });
     }
     if (user.value?.role !== 'admin') {
       return abortNavigation(createError({ statusCode: 403, statusMessage: 'Forbidden' }));
     }
   });
   ```

   - Return `navigateTo(...)` or `abortNavigation(...)`; return nothing to continue.
     Don't call `router.push`.
   - Use composables inside the function, never at module scope.
   - A global middleware that redirects must skip its own target (`if (to.path === '/login') return;`)
     or it loops.
   - Code runs on server and client: no `window` without `import.meta.client`.
   - Async work (fetching the session, a flag) is fine: `await` it inside.
3. **Wire it**: named middleware is opt-in per page:

   ```ts
   definePageMeta({ middleware: ['auth', 'admin'] });
   ```

   Global middleware (`*.global.ts`) runs on every navigation, in alphabetical order
   (prefix with numbers to order: `01.auth.global.ts`).
4. **Test** in `tests/nuxt/middleware/<name>.test.ts`: `mockNuxtImport` the
   composables it reads, call the middleware with a fake `to` route, assert the
   redirect (or that it returns nothing). Pair it with a server-route test proving
   the data is protected without it.
5. **Run**: `npx nuxi typecheck && npm run lint && npx vitest run`

## Generated Files

```
app/middleware/<name>[.global].ts
tests/nuxt/middleware/<name>.test.ts
```
