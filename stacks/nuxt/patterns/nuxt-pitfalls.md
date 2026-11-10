# Nuxt 4 Pitfalls

Read this when debugging hydration warnings, double requests, stale data, or code
that works on the client and breaks on the server.

## 1. Hydration Mismatches

The server HTML and the first client render must match. Causes:

| Cause | Fix |
|---|---|
| `Date.now()`, `new Date()`, `Math.random()` in the template/setup | Compute once in `useState` / `useAsyncData` (serialized to the client), or render in `<ClientOnly>` |
| `window`, `localStorage`, `matchMedia` read during setup | Read in `onMounted`, or `import.meta.client` guard + `<ClientOnly>` |
| Locale/timezone formatting (`toLocaleString()`) | Pass an explicit locale and `timeZone`, or format on the server |
| Invalid HTML (`<div>` inside `<p>`, `<a>` inside `<a>`, tables without `<tbody>`) | Fix the markup; the browser rewrites it and Vue sees a different tree |
| Auth state only known on the client | Read the session on the server (`useUserSession()` is SSR-aware) |

```vue
<!-- WRONG: differs between server and client -->
<span>{{ new Date().toLocaleTimeString() }}</span>

<!-- RIGHT -->
<ClientOnly>
  <LocalTime />
  <template #fallback><span>--:--</span></template>
</ClientOnly>
```

## 2. `useFetch` / `useAsyncData` Keys and Timing

- **Called after setup** (click handler, `onMounted`, `watch` callback): no SSR,
  no dedupe, warnings. Use `$fetch` there; `refresh()` to reload a `useFetch`.
- **Same key, different data**: two calls sharing a key share one payload entry.
  Give explicit, unique keys in composables: ``useAsyncData(`project-${id}`, ...)``.
- **Reactive inputs**: pass a ref/getter, not `.value`, so the request re-runs:
  `useFetch('/api/projects', { query: { page } })` (with `page` a ref) or
  ``useFetch(() => `/api/projects/${route.params.id}`)``.
- **`$fetch` directly in setup** runs twice (server, then client again on hydration).
  Wrap it: `useAsyncData('key', () => $fetch(...))`.
- **Shared data object**: `data` from `useFetch` with the same key is the same ref
  across components; don't mutate it in place unless that's intended.
- Read `status` (`'idle' | 'pending' | 'success' | 'error'`), not the removed `pending`.
- `data` defaults to `undefined` (Nuxt 4): give `default: () => []` when the template
  expects an array.

## 3. Client-Only and Server-Only APIs

| Need | Do |
|---|---|
| Browser API in a composable | Guard with `if (import.meta.client)` or move to `onMounted` |
| Browser-only library (charts, editors) | `<ClientOnly>` + a `.client.vue` component, or a `.client.ts` plugin |
| Server-only code (DB, secrets) | `server/` only; never import it from `app/` |
| Request headers/cookies during SSR | `useRequestHeaders(['cookie'])`, `useCookie`, `useRequestEvent()` |

During SSR, plain `$fetch('/api/...')` does not forward the visitor's cookies, so
authenticated routes answer 401. `useFetch` forwards them; for imperative calls that
may run on the server use `const requestFetch = useRequestFetch()`.

## 4. Cross-Request State Pollution

Module-level `ref`s, arrays or objects in composables/plugins live in the server
process and are shared by every user:

```ts
// WRONG: shared by all SSR requests
const currentUser = ref<User | null>(null);
export function useCurrentUser() { return currentUser; }

// RIGHT: per-request, serialized to the client
export function useCurrentUser() {
  return useState<User | null>('current-user', () => null);
}
```

`useState` values must be serializable (no class instances, functions, Maps).

## 5. Composables Outside the Nuxt Context

`useRuntimeConfig`, `useNuxtApp`, `useRoute`, `useState` need the Nuxt context:
call them in setup, middleware, plugins or other composables, synchronously, before
the first `await` that isn't a Nuxt helper. In server routes use the H3 `event`
versions (`useRuntimeConfig(event)`).

## 6. Middleware

- Return `navigateTo(...)` / `abortNavigation()`; don't call `router.push`.
- Avoid redirect loops: a global middleware sending to `/login` must skip `/login`.
- Middleware runs on the server for the first request and on the client after:
  code must work in both.

## 7. Auto-Imports

- Components are named by path (`components/project/Card.vue` → `<ProjectCard>`).
- Name clashes between a composable and a util are silent; keep names unique.
- Type errors after adding files: run `npx nuxi prepare` (regenerates `.nuxt` types).
