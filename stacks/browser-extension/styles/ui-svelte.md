# Svelte UI Conventions (Browser Extension)

How to build popup / options / side-panel surfaces with Svelte 5 inside a WXT extension.
`@wxt-dev/module-svelte` is enabled in `wxt.config.ts`. Type checking is `svelte-check`
(`npm run compile`). Use runes (`$state`, `$derived`, `$effect`, `$props`), not the
Svelte 4 `export let` / `$:` syntax.

## 1. Mount one Svelte app per surface

```typescript
// entrypoints/popup/main.ts
import { mount } from 'svelte';
import App from './App.svelte';
import './style.css';

mount(App, { target: document.getElementById('app')! });
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

## 2. Read extension state with a rune-based helper

Runes outside components need a `.svelte.ts` file.

```typescript
// lib/storage-state.svelte.ts
import type { WxtStorageItem } from 'wxt/utils/storage';

/** Call during component initialisation (it registers an $effect). */
export function storageState<T>(item: WxtStorageItem<T, any>) {
  let value = $state<T | null>(null);

  $effect(() => {
    item.getValue().then((v) => (value = v));
    return item.watch((next) => (value = next)); // cleanup runs on unmount
  });

  return {
    get value() {
      return value;
    },
    set: (next: T) => item.setValue(next),
  };
}
```

```svelte
<!-- entrypoints/popup/App.svelte -->
<script lang="ts">
  import { settings } from '@/utils/storage';
  import { storageState } from '@/lib/storage-state.svelte';

  const theme = storageState(settings);

  function toggleTheme() {
    if (!theme.value) return;
    theme.set({ ...theme.value, theme: theme.value.theme === 'light' ? 'dark' : 'light' });
  }
</script>

{#if theme.value}
  <button type="button" onclick={toggleTheme}>Theme: {theme.value.theme}</button>
{/if}
```

## 3. Call the background through typed messaging

```svelte
<script lang="ts">
  import { sendMessage } from '@/utils/messaging';

  const tab = sendMessage('getActiveTab', undefined);
</script>

{#await tab then t}
  <p>{t.title ?? 'No active tab'}</p>
{/await}
```

## 4. Content-script Svelte lives in a Shadow Root

```typescript
// entrypoints/overlay.content/index.ts
import { mount, unmount } from 'svelte';
import Overlay from './Overlay.svelte';
import './style.css';

export default defineContentScript({
  matches: ['*://*.example.com/*'],
  cssInjectionMode: 'ui',
  async main(ctx) {
    const ui = await createShadowRootUi(ctx, {
      name: 'my-overlay',
      position: 'inline',
      anchor: 'body',
      onMount: (container) => mount(Overlay, { target: container }),
      onRemove: (app) => {
        if (app) unmount(app);
      },
    });
    ui.mount();
  },
});
```

## 5. Component conventions

- Components are `PascalCase.svelte` with `<script lang="ts">`; props via
  `let { title }: { title: string } = $props();`.
- Shared reactive helpers live in `lib/*.svelte.ts`.
- Events are plain props (`onclick`, `onsave`), not `on:click` / `createEventDispatcher`.
- A popup has a fixed width; set it on `body` in the surface's CSS.

## 6. Don't

- `chrome.storage.local.get` in a component; use `wxt/utils/storage` via a helper.
- Long-lived timers in a popup: it is destroyed when it closes.
- `{@html ...}` with page or user content (see `.claude/patterns/security.md`).
