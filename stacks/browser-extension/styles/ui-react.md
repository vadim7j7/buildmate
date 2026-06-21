# React UI Conventions (Browser Extension)

How to build popup / options / side-panel surfaces with React inside a WXT extension.
The `@wxt-dev/module-react` module is enabled in `wxt.config.ts`, so JSX, fast refresh,
and the React preset work out of the box.

## 1. Mount one React app per surface

Each UI entrypoint is a folder with `index.html` + `main.tsx`. Keep the HTML minimal and
mount React into `#app`.

CORRECT:

```tsx
// entrypoints/popup/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './style.css';

ReactDOM.createRoot(document.getElementById('app')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
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
    <script type="module" src="./main.tsx"></script>
  </body>
</html>
```

WRONG — do not call extension APIs at module scope before React mounts, and do not
share one root across surfaces.

## 2. Read extension state with a hook, not at import time

Wrap `wxt/storage` and messaging in hooks so components re-render reactively and the
popup unmounts cleanly.

```tsx
// hooks/useStorageItem.ts
import { useEffect, useState } from 'react';
import type { WxtStorageItem } from 'wxt/storage';

export function useStorageItem<T>(item: WxtStorageItem<T, any>) {
  const [value, setValue] = useState<T | null>(null);

  useEffect(() => {
    item.getValue().then(setValue);
    const unwatch = item.watch(setValue);
    return unwatch; // detach on unmount — popups mount/unmount constantly
  }, [item]);

  return [value, item.setValue] as const;
}
```

```tsx
// entrypoints/popup/App.tsx
import { settings } from '@/utils/storage';
import { useStorageItem } from '@/hooks/useStorageItem';

export default function App() {
  const [value, setValue] = useStorageItem(settings);
  if (!value) return null;

  return (
    <button onClick={() => setValue({ ...value, theme: value.theme === 'light' ? 'dark' : 'light' })}>
      Theme: {value.theme}
    </button>
  );
}
```

## 3. Call the background through typed messaging

Never reach into `browser.*` privileged APIs directly from a popup when the background
already owns that capability — call it through the shared protocol.

```tsx
import { useEffect, useState } from 'react';
import { sendMessage } from '@/utils/messaging';

export function useActiveTab() {
  const [tab, setTab] = useState<{ title?: string } | null>(null);
  useEffect(() => {
    sendMessage('getActiveTab', undefined).then(setTab);
  }, []);
  return tab;
}
```

## 4. Content-script React lives in a Shadow Root

When you render React **into a page** from a content script, mount it inside
`createShadowRootUi(ctx, ...)` so the host page's CSS can't leak in and yours can't leak
out. Tie the React root's lifecycle to `ctx`.

```tsx
// entrypoints/overlay.content.tsx
import ReactDOM from 'react-dom/client';
import Overlay from './Overlay';

export default defineContentScript({
  matches: ['*://*.example.com/*'],
  cssInjectionMode: 'ui',
  async main(ctx) {
    const ui = await createShadowRootUi(ctx, {
      name: 'my-overlay',
      position: 'inline',
      onMount(container) {
        const root = ReactDOM.createRoot(container);
        root.render(<Overlay />);
        return root;
      },
      onRemove(root) {
        root?.unmount();
      },
    });
    ui.mount();
  },
});
```

## 5. Component conventions

- Components are `PascalCase.tsx`; hooks are `useThing.ts` under `hooks/`.
- Keep surfaces thin: data access in hooks, presentation in components.
- A popup has a fixed width (e.g. 320px) — set it on `body`, not the root component.
- Prefer CSS Modules or a single `style.css` per surface; avoid inline style objects.
- Type all props; no `any`. Strict mode is on.

## 6. Don't

- ❌ `chrome.storage.local.get` in a component — use `wxt/storage` via a hook.
- ❌ Long-lived timers in a popup — the popup is destroyed when it closes.
- ❌ `dangerouslySetInnerHTML` with page/user content — see `styles/extension.md` and
  `patterns/security.md`.
