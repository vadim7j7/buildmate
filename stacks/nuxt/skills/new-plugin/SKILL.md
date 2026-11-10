---
name: new-plugin
description: Generate a Nuxt 4 runtime plugin (provide helpers, wrap a library, client- or server-only)
---

# /new-plugin

## What This Does

Generates a plugin in `app/plugins/` that runs once when the Nuxt app starts: to
provide a typed helper (`useNuxtApp().$api`), register a Vue plugin or directive,
set up a browser-only library, or hook into app lifecycle events.

Reach for a plugin only when a composable won't do: a composable is the default
for shared logic. Server-wide request hooks belong in `server/plugins/` (Nitro),
not here.

## Usage

```
/new-plugin api             # app/plugins/api.ts: $fetch instance with base URL + auth
/new-plugin analytics       # app/plugins/analytics.client.ts (browser only)
/new-plugin error-reporter  # app/plugins/error-reporter.ts (vue:error / app:error hooks)
```

## How It Works

1. **Read** existing `app/plugins/` and `nuxt.config.ts` (`runtimeConfig`, modules).
   Check first whether a Nuxt module already does the job (`npx nuxi module add ...`).
2. **Generate the plugin** with `defineNuxtPlugin` (object syntax when it needs a name,
   order or `dependsOn`):

   ```ts
   // app/plugins/api.ts
   export default defineNuxtPlugin({
     name: 'api',
     setup(nuxtApp) {
       const config = useRuntimeConfig();
       const headers = useRequestHeaders(['cookie']); // forward the visitor's cookie during SSR

       const api = $fetch.create({
         baseURL: config.public.apiBase,
         headers,
         onResponseError({ response }) {
           if (response.status === 401) {
             // runs outside setup: restore the Nuxt context before navigating
             return nuxtApp.runWithContext(() => navigateTo('/login'));
           }
         },
       });

       return { provide: { api } }; // typed as useNuxtApp().$api
     },
   });
   ```

   ```ts
   // app/plugins/analytics.client.ts
   export default defineNuxtPlugin(() => {
     const { public: { analyticsKey } } = useRuntimeConfig();
     if (!analyticsKey) return;
     const router = useRouter();
     router.afterEach((to) => trackPageView(analyticsKey, to.fullPath)); // your SDK call
   });
   ```

   - Suffix `.client.ts` / `.server.ts` for one side only.
   - No secrets: plugins on the client only see `runtimeConfig.public`.
   - Keep setup fast and non-blocking (it delays every page); use `parallel: true`
     for independent async plugins.
   - No module-level mutable state (shared across SSR requests).
   - Wrap the provided helper in a composable (`useApi()`) for nicer call sites.
3. **Test** what the plugin provides in the Nuxt environment (`tests/nuxt/plugins/`):
   `useNuxtApp().$api` exists, with `registerEndpoint` faking the API.
4. **Run**: `npx nuxi typecheck && npm run lint && npx vitest run`

## Generated Files

```
app/plugins/<name>[.client|.server].ts
tests/nuxt/plugins/<name>.test.ts
```
