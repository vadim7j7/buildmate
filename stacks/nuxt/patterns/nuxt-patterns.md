# Nuxt 3 Code Patterns

Reference patterns for Nuxt 3 development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Page Pattern

Pages use file-based routing with `<script setup>` and `useFetch`.

```vue
<!-- pages/projects/index.vue -->
<script setup lang="ts">
definePageMeta({
  title: 'Projects',
});

const { data: projects, pending, error, refresh } = await useFetch('/api/projects');
</script>

<template>
  <div>
    <h1>Projects</h1>
    <div v-if="pending">Loading...</div>
    <div v-else-if="error">Error: {{ error.message }}</div>
    <ProjectList v-else :projects="projects ?? []" />
  </div>
</template>
```

### Dynamic Page

```vue
<!-- pages/projects/[id].vue -->
<script setup lang="ts">
const route = useRoute();
const { data: project, error } = await useFetch(`/api/projects/${route.params.id}`);

if (error.value) {
  throw createError({ statusCode: 404, statusMessage: 'Project not found' });
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

Extract reusable logic into composables.

```typescript
// composables/useProjects.ts
export function useProjects() {
  const projects = ref<Project[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchProjects() {
    loading.value = true;
    error.value = null;
    try {
      projects.value = await $fetch('/api/projects');
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error';
    } finally {
      loading.value = false;
    }
  }

  async function createProject(data: { name: string; description?: string }) {
    return $fetch('/api/projects', { method: 'POST', body: data });
  }

  return { projects, loading, error, fetchProjects, createProject };
}
```

### Rules

- Prefix with `use` (e.g., `useProjects`, `useAuth`)
- Return reactive refs and methods
- Handle loading and error states internally
- Use `$fetch` for imperative calls, `useFetch` for SSR-compatible calls

---

## 3. Server Route Pattern

Server routes live in `server/api/` with file-based routing.

```typescript
// server/api/projects/index.get.ts
export default defineEventHandler(async (event) => {
  const query = getQuery(event);
  const skip = Number(query.skip ?? 0);
  const limit = Number(query.limit ?? 20);

  return db.project.findMany({ skip, take: limit });
});

// server/api/projects/index.post.ts
export default defineEventHandler(async (event) => {
  const body = await readBody(event);
  const project = await db.project.create({ data: body });
  setResponseStatus(event, 201);
  return project;
});

// server/api/projects/[id].get.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');
  const project = await db.project.findUnique({ where: { id } });

  if (!project) {
    throw createError({ statusCode: 404, statusMessage: 'Not found' });
  }

  return project;
});

// server/api/projects/[id].patch.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');
  const body = await readBody(event);
  return db.project.update({ where: { id }, data: body });
});

// server/api/projects/[id].delete.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');
  await db.project.delete({ where: { id } });
  setResponseStatus(event, 204);
  return null;
});
```

### Rules

- Use HTTP method suffix (`.get.ts`, `.post.ts`, `.patch.ts`, `.delete.ts`)
- Use `defineEventHandler` for all handlers
- Use `getQuery`, `readBody`, `getRouterParam` for input
- Use `createError` for error responses
- Use `setResponseStatus` for non-200 status codes

---

## 4. Pinia Store Pattern

```typescript
// stores/auth.ts
export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const isAuthenticated = computed(() => user.value !== null);

  async function login(email: string, password: string) {
    const response = await $fetch('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    });
    user.value = response.user;
  }

  function logout() {
    user.value = null;
    navigateTo('/login');
  }

  return { user, isAuthenticated, login, logout };
});
```

### Rules

- Use `defineStore` with Composition API (not Options API)
- Name stores with `use` prefix
- Return only what consumers need
- Use `$fetch` for API calls within stores

---

## 5. Middleware Pattern

```typescript
// middleware/auth.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const auth = useAuthStore();

  if (!auth.isAuthenticated) {
    return navigateTo('/login');
  }
});
```

---

## 6. Layout Pattern

```vue
<!-- layouts/default.vue -->
<script setup lang="ts">
const auth = useAuthStore();
</script>

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
<!-- components/ProjectCard.vue -->
<script setup lang="ts">
type Props = {
  project: Project;
  showActions?: boolean;
};

const props = withDefaults(defineProps<Props>(), {
  showActions: true,
});

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
