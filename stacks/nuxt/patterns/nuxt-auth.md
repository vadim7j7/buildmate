# Authentication in Nuxt 4 (nuxt-auth-utils)

Read this when a task adds sign-in, sessions, OAuth, or protects pages or server
routes. Use `nuxt-auth-utils` (sealed cookie sessions, OAuth providers, password
hashing) unless the project already has another auth setup; then follow that.

If a separate backend (Rails, Django, FastAPI, Express...) owns users, the session
holds that backend's token: the Nuxt server forwards it, the backend authorizes.

## Setup

```bash
npx nuxi module add auth-utils
```

```bash
# .env: 32+ random characters; different per environment; never committed
NUXT_SESSION_PASSWORD=...
```

```ts
// shared/types/auth.d.ts: type what lives in the session
declare module '#auth-utils' {
  interface User {
    id: string;
    email: string;
    role: 'admin' | 'member';
  }
  interface SecureSessionData {
    apiToken?: string; // server-only: never sent to the client
  }
}
export {};
```

## Sign In / Out (server)

```ts
// server/api/auth/login.post.ts
import { z } from 'zod';

const Body = z.object({ email: z.email(), password: z.string().min(8) });

export default defineEventHandler(async (event) => {
  const { email, password } = await readValidatedBody(event, Body.parse);
  const user = await db.user.findUnique({ where: { email } });

  // Same error for unknown email and wrong password
  if (!user || !(await verifyPassword(user.passwordHash, password))) {
    throw createError({ statusCode: 401, statusMessage: 'Invalid credentials' });
  }

  await setUserSession(event, {
    user: { id: user.id, email: user.email, role: user.role },
    loggedInAt: Date.now(),
  });
  return { ok: true };
});

// server/api/auth/logout.post.ts
export default defineEventHandler(async (event) => {
  await clearUserSession(event);
  return { ok: true };
});
```

Hash new passwords with `await hashPassword(password)`. A backend token goes in the
server-only part: `setUserSession(event, { user, secure: { apiToken } })`.

## OAuth

```ts
// server/routes/auth/github.get.ts
export default defineOAuthGitHubEventHandler({
  async onSuccess(event, { user: gh }) {
    const user = await upsertUserFromGitHub(gh);
    await setUserSession(event, { user: { id: user.id, email: user.email, role: user.role } });
    return sendRedirect(event, '/');
  },
  onError(event, error) {
    console.error('GitHub OAuth error', error);
    return sendRedirect(event, '/login?error=oauth');
  },
});
```

Provider credentials come from env (`NUXT_OAUTH_GITHUB_CLIENT_ID`, `..._CLIENT_SECRET`).

## Protecting Server Routes (the real boundary)

Every handler that reads or changes private data checks the session itself:

```ts
// server/utils/auth.ts (auto-imported in server/)
import type { H3Event } from 'h3';
import type { User } from '#auth-utils';

export async function requireUser(event: H3Event) {
  const { user } = await requireUserSession(event); // 401 when signed out
  return user;
}

export async function requireRole(event: H3Event, role: User['role']) {
  const user = await requireUser(event);
  if (user.role !== role) throw createError({ statusCode: 403, statusMessage: 'Forbidden' });
  return user;
}
```

Scope queries by owner/tenant: `where: { id, ownerId: user.id }`; a 404 for
someone else's record is better than a 403 that confirms it exists.

## Protecting Pages (UX only)

```ts
// app/middleware/auth.ts
export default defineNuxtRouteMiddleware((to) => {
  const { loggedIn } = useUserSession();
  if (!loggedIn.value) {
    return navigateTo({ path: '/login', query: { redirect: to.fullPath } });
  }
});
```

```vue
<script setup lang="ts">
definePageMeta({ middleware: 'auth' });
const { user, clear } = useUserSession();

async function logout() {
  await $fetch('/api/auth/logout', { method: 'POST' });
  await clear();
  await navigateTo('/login');
}
</script>
```

Route middleware hides pages; it does not protect data. A page guard without a
server-route check is a security bug.

## Rules

- Validate the `redirect` query before using it (relative paths only) to avoid open redirects.
- Rate-limit login, sign-up and password reset (see `nuxt-security.md`).
- Rotate the session after sign-in (`setUserSession` replaces it) and clear it on sign-out.
- Tokens for a backend API go in `secure` session data, never in `user` (which the client sees).
