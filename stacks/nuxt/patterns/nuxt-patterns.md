# Nuxt 4 Code Patterns

Reference patterns for Nuxt 4 development. Agents should read this file
before writing code to ensure consistency across the codebase.

## Directory Layout (Nuxt 4)

Nuxt 4 puts the app code in `app/`; `server/`, `shared/` and `public/` stay at the root.

```
app/
  app.vue
  pages/          # file-based routes
  layouts/
  components/
  composables/
  middleware/     # route middleware
  plugins/        # runtime plugins (*.client.ts / *.server.ts for one side)
  stores/         # Pinia stores (if the project uses Pinia)
  utils/
server/
  api/            # API routes (Nitro)
  utils/          # auto-imported server helpers (e.g. requireUser)
shared/           # code/types shared by app and server
tests/            # Vitest (unit + nuxt environments)
nuxt.config.ts
```

If a project still has `pages/` etc. at the root (Nuxt 3 layout or
`future.compatibilityVersion` settings), follow what the project uses.

---

## 1. Page Pattern

Pages use file-based routing with `<script setup>` and `useFetch` (SSR-safe,
deduplicated between server and client). `useFetch` returns `status`
(`'idle' | 'pending' | 'success' | 'error'`), not the removed `pending` flag.

```vue
<!-- app/pages/projects/index.vue -->
<script setup lang="ts">
useHead({ title: 'Projects' });

const { data: projects, status, error, refresh } = await useFetch('/api/projects');
</script>

<template>
  <div>
    <h1>Projects</h1>
    <div v-if="status === 'pending'">Loading...</div>
    <div v-else-if="error">Error: {{ error.message }}</div>
    <ProjectList v-else :projects="projects ?? []" @changed="refresh" />
  </div>
</template>
```

### Dynamic Page

```vue
<!-- app/pages/projects/[id].vue -->
<script setup lang="ts">
const route = useRoute();
const id = computed(() => String(route.params.id));

const { data: project, error } = await useFetch(() => `/api/projects/${id.value}`);

if (error.value) {
  throw createError({ statusCode: 404, statusMessage: 'Project not found', fatal: true });
}
</script>

<template>
  <div v-if="project">
    <h1>{{ project.name }}</h1>
    <p>{{ project.description }}</p>
  </div>
</template>
```

---

## 2. Composable Pattern

Two kinds of composables:

- **Data composables** wrap `useFetch` / `useAsyncData`. They must be called
  synchronously in `<script setup>` (or another composable), never inside a function
  that runs later (click handler, `onMounted`, after an `await` in a plain function).
- **Action composables** expose functions that call `$fetch` imperatively
  (mutations, user-triggered loads).

```typescript
// app/composables/useProjects.ts
export function useProjects() {
  // SSR-safe read: called during setup.
  const { data: projects, status, error, refresh } = useFetch('/api/projects', {
    key: 'projects',
    default: () => [] as Project[],
  });

  // Imperative mutation: $fetch, not useFetch.
  async function createProject(input: { name: string; description?: string }) {
    const project = await $fetch('/api/projects', { method: 'POST', body: input });
    await refresh();
    return project;
  }

  async function deleteProject(id: string) {
    await $fetch(`/api/projects/${id}`, { method: 'DELETE' });
    await refresh();
  }

  return { projects, status, error, refresh, createProject, deleteProject };
}
```

### Rules

- Prefix with `use` (e.g., `useProjects`, `useAuth`)
- Return reactive refs and methods
- `useFetch` / `useAsyncData` only at setup time; `$fetch` inside functions run later
- Expose `status` from `useFetch` (not a hand-rolled `loading` ref)

---

## 3. Server Route Pattern

Server routes live in `server/api/` with file-based routing. Validate every input
with a schema (`readValidatedBody`, `getValidatedQuery`, `getValidatedRouterParams`)
and check auth in the handler.

```typescript
// server/utils/auth.ts (auto-imported in server/)
export async function requireUser(event: H3Event) {
  const user = event.context.user; // set by your auth (e.g. nuxt-auth-utils' requireUserSession)
  if (!user) throw createError({ statusCode: 401, statusMessage: 'Unauthorized' });
  return user;
}
```

```typescript
// shared/schemas/project.ts
import { z } from 'zod';

export const projectInput = z.object({
  name: z.string().trim().min(2).max(100),
  description: z.string().trim().max(1000).optional(),
});
export const projectQuery = z.object({
  skip: z.coerce.number().int().min(0).default(0),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});
export const projectParams = z.object({ id: z.string().uuid() });
```

```typescript
// server/api/projects/index.get.ts
import { projectQuery } from '#shared/schemas/project';

export default defineEventHandler(async (event) => {
  const user = await requireUser(event);
  const { skip, limit } = await getValidatedQuery(event, projectQuery.parse);

  return db.project.findMany({ where: { ownerId: user.id }, skip, take: limit });
});

// server/api/projects/index.post.ts
import { projectInput } from '#shared/schemas/project';

export default defineEventHandler(async (event) => {
  const user = await requireUser(event);
  const body = await readValidatedBody(event, projectInput.parse);

  const project = await db.project.create({ data: { ...body, ownerId: user.id } });
  setResponseStatus(event, 201);
  return project;
});

// server/api/projects/[id].get.ts
import { projectParams } from '#shared/schemas/project';

export default defineEventHandler(async (event) => {
  const user = await requireUser(event);
  const { id } = await getValidatedRouterParams(event, projectParams.parse);
  const project = await db.project.findFirst({ where: { id, ownerId: user.id } });

  if (!project) {
    throw createError({ statusCode: 404, statusMessage: 'Not found' });
  }

  return project;
});

// server/api/projects/[id].patch.ts
import { projectInput, projectParams } from '#shared/schemas/project';

export default defineEventHandler(async (event) => {
  const user = await requireUser(event);
  const { id } = await getValidatedRouterParams(event, projectParams.parse);
  const body = await readValidatedBody(event, projectInput.partial().parse);

  const { count } = await db.project.updateMany({ where: { id, ownerId: user.id }, data: body });
  if (count === 0) throw createError({ statusCode: 404, statusMessage: 'Not found' });
  return db.project.findUnique({ where: { id } });
});

// server/api/projects/[id].delete.ts
import { projectParams } from '#shared/schemas/project';

export default defineEventHandler(async (event) => {
  const user = await requireUser(event);
  const { id } = await getValidatedRouterParams(event, projectParams.parse);

  const { count } = await db.project.deleteMany({ where: { id, ownerId: user.id } });
  if (count === 0) throw createError({ statusCode: 404, statusMessage: 'Not found' });
  setResponseStatus(event, 204);
  return null;
});
```

### Rules

- Use HTTP method suffix (`.get.ts`, `.post.ts`, `.patch.ts`, `.delete.ts`)
- Use `defineEventHandler` for all handlers
- Validate input with `readValidatedBody(event, schema.parse)`, `getValidatedQuery`,
  `getValidatedRouterParams` — not plain `readBody` / `getQuery`
- Authenticate and authorize in every handler that reads or changes private data
- Use `createError` for error responses (a Zod failure becomes a 400 automatically)
- Use `setResponseStatus` for non-200 status codes

---

## 4. Shared State

Server data a page reads stays in `useFetch` / `useAsyncData`. For small shared
state, use `useState` (SSR-safe, serialized to the client, one copy per request):

```typescript
// app/composables/useSidebar.ts
export function useSidebar() {
  const open = useState('sidebar-open', () => false);
  const toggle = () => { open.value = !open.value; };
  return { open, toggle };
}
```

Never keep state in a module-level `ref`: on the server it is shared by every
request. If the project uses Pinia, stores follow `pinia.md`.

---

## 5. Route Middleware Pattern

Route middleware only guards navigation; server routes still check auth themselves.

```typescript
// app/middleware/auth.ts
export default defineNuxtRouteMiddleware((to) => {
  const { loggedIn } = useUserSession(); // nuxt-auth-utils; see nuxt-auth.md

  if (!loggedIn.value) {
    return navigateTo({ path: '/login', query: { redirect: to.fullPath } });
  }
});
```

Pages opt in with `definePageMeta({ middleware: 'auth' })`; a file named
`*.global.ts` runs on every navigation.

---

## 6. Layout Pattern

```vue
<!-- app/layouts/default.vue -->
<template>
  <div class="layout">
    <AppHeader />
    <main>
      <slot />
    </main>
    <AppFooter />
  </div>
</template>
```

---

## 7. Component Pattern

```vue
<!-- app/components/ProjectCard.vue -->
<script setup lang="ts">
type Props = {
  project: Project;
  showActions?: boolean;
};

const { project, showActions = true } = defineProps<Props>();

const emit = defineEmits<{
  delete: [id: string];
}>();
</script>

<template>
  <div class="project-card">
    <h3>{{ project.name }}</h3>
    <p>{{ project.description }}</p>
    <button v-if="showActions" @click="emit('delete', project.id)">
      Delete
    </button>
  </div>
</template>
```

---

## 8. Tooling

- **Typecheck**: `npx nuxi typecheck` (runs `vue-tsc` over `.vue` files with the
  generated `.nuxt` tsconfigs). Needs `vue-tsc` and `typescript` as dev dependencies.
  Plain `npx tsc --noEmit` does not check `.vue` files and, with Nuxt 4's root
  `tsconfig.json` holding only project references, checks nothing useful.
- **Lint**: `@nuxt/eslint` module + an `eslint.config.mjs` that exports
  `withNuxt()`, and a `"lint": "eslint ."` script in `package.json`.
- **Tests**: Vitest with `@nuxt/test-utils` (see the tester agent).
