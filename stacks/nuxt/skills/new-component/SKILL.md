---
name: new-component
description: Generate a typed Vue 3 component for Nuxt 4 with props, emits, slots and a test
---

# /new-component

## What This Does

Generates a Vue 3 single-file component in `app/components/` with typed props and
emits (`<script setup lang="ts">`), and a component test that mounts it in the Nuxt
environment.

## Usage

```
/new-component ProjectCard          # app/components/ProjectCard.vue
/new-component project/StatusBadge  # app/components/project/StatusBadge.vue → <ProjectStatusBadge>
/new-component Chart --client       # app/components/Chart.client.vue (browser-only)
```

## How It Works

1. **Read** `.claude/patterns/nuxt-patterns.md` (Component Pattern) and grep
   `app/components/` for a similar component; match its structure and styling.
2. **Generate the component**:

   ```vue
   <script setup lang="ts">
   type Props = {
     project: Project;
     showActions?: boolean;
   };

   // Vue 3.5 reactive props destructure with defaults
   const { project, showActions = true } = defineProps<Props>();

   const emit = defineEmits<{
     delete: [id: string];
   }>();

   const model = defineModel<boolean>('open', { default: false }); // only if it has a v-model
   </script>

   <template>
     <article>
       <h3>{{ project.name }}</h3>
       <slot name="meta" :project="project" />
       <button v-if="showActions" type="button" @click="emit('delete', project.id)">
         Delete
       </button>
     </article>
   </template>
   ```

   - Presentational by default: data comes in as props, changes go out as emits.
     A component that loads its own data calls a composable (`/new-composable`).
   - No browser APIs in setup (`window`, `localStorage`): use `onMounted`, or make it
     a `.client.vue` component (rendered only in the browser; wrap usages in `<ClientOnly>`
     with a `#fallback` to avoid layout shift).
   - Heavy or below-the-fold components are used as `<LazyName>` (auto code-split).
   - Accessible markup: real `<button>` / `<a>`, labels for inputs, `alt` on images.
   - The name comes from the path; don't import components manually (auto-imports).
3. **Generate a test** `tests/nuxt/components/<Name>.test.ts` with `mountSuspended`:
   renders props, emits events with the right payload, renders slots, hides optional
   parts (see `nuxt-testing.md` if installed).
4. **Run**: `npx nuxi typecheck && npm run lint && npx vitest run`

## Generated Files

```
app/components/<path>/<Name>.vue
tests/nuxt/components/<Name>.test.ts
```

Follow the project's existing test folder if it differs.
