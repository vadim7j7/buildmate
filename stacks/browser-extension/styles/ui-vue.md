# Vue UI Conventions (Browser Extension)

How to build popup / options / side-panel surfaces with Vue 3 inside a WXT extension.
`@wxt-dev/module-vue` is enabled in `wxt.config.ts`, so `.vue` SFCs, the Vue Vite plugin
and auto-imports work out of the box. Type checking is `vue-tsc` (`npm run compile`).

## 1. Mount one Vue app per surface

Each UI entrypoint is a folder with `index.html` + `main.ts` + `App.vue`.

```typescript
// entrypoints/popup/main.ts
import { createApp } from 'vue';
import App from './App.vue';
import './style.css';

createApp(App).mount('#app');
```

```html
<!-- entrypoints/popup/index.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Popup</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="./main.ts"></script>
  </body>
</html>
```

Don't call extension APIs at module scope before the app mounts, and don't share one
app instance across surfaces.

## 2. Read extension state with a composable

Wrap `wxt/utils/storage` in a composable so components update reactively and the
watcher is removed when the popup closes.

```typescript
// composables/useStorageItem.ts
import { onMounted, onUnmounted, ref, type Ref } from 'vue';
import type { WxtStorageItem } from 'wxt/utils/storage';

export function useStorageItem<T>(item: WxtStorageItem<T, any>) {
  const value = ref<T | null>(null) as Ref<T | null>;
  let unwatch: (() => void) | undefined;

  onMounted(async () => {
    value.value = await item.getValue();
    unwatch = item.watch((next) => (value.value = next));
  });
  onUnmounted(() => unwatch?.()); // popups mount/unmount constantly

  return { value, set: (next: T) => item.setValue(next) };
}
```

```vue
<!-- entrypoints/popup/App.vue -->
<script setup lang="ts">
import { settings } from '@/utils/storage';
import { useStorageItem } from '@/composables/useStorageItem';

const { value, set } = useStorageItem(settings);

function toggleTheme() {
  if (!value.value) return;
  set({ ...value.value, theme: value.value.theme === 'light' ? 'dark' : 'light' });
}
</script>

<template>
  <button v-if="value" type="button" @click="toggleTheme">Theme: {{ value.theme }}</button>
</template>
```

## 3. Call the background through typed messaging

```typescript
// composables/useActiveTab.ts
import { onMounted, ref } from 'vue';
import { sendMessage } from '@/utils/messaging';

export function useActiveTab() {
  const tab = ref<{ title?: string } | null>(null);
  onMounted(async () => {
    tab.value = await sendMessage('getActiveTab', undefined);
  });
  return tab;
}
```

## 4. Content-script Vue lives in a Shadow Root

```typescript
// entrypoints/overlay.content/index.ts
import { createApp } from 'vue';
import Overlay from './Overlay.vue';
import './style.css';

export default defineContentScript({
  matches: ['*://*.example.com/*'],
  cssInjectionMode: 'ui',
  async main(ctx) {
    const ui = await createShadowRootUi(ctx, {
      name: 'my-overlay',
      position: 'inline',
      anchor: 'body',
      onMount(container) {
        const app = createApp(Overlay);
        app.mount(container);
        return app;
      },
      onRemove(app) {
        app?.unmount();
      },
    });
    ui.mount();
  },
});
```

## 5. Component conventions

- SFCs are `PascalCase.vue` with `<script setup lang="ts">`; composables are
  `useThing.ts` under `composables/`.
- Keep surfaces thin: data access in composables, presentation in components.
- Props typed with `defineProps<{ ... }>()`; emits with `defineEmits<{ ... }>()`.
- A popup has a fixed width; set it on `body` in the surface's CSS.
- Scoped styles (`<style scoped>`) or one `style.css` per surface.

## 6. Don't

- `chrome.storage.local.get` in a component; use `wxt/utils/storage` via a composable.
- Long-lived timers in a popup: it is destroyed when it closes.
- `v-html` with page or user content (see `.claude/patterns/security.md`).
