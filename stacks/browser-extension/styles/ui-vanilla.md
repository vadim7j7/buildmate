# Vanilla TypeScript UI Conventions (Browser Extension)

The UI surfaces (popup / options / side panel) use no framework: plain TypeScript and
the DOM. The scaffolded `entrypoints/popup/main.ts` is the reference.

## 1. One `main.ts` per surface

```html
<!-- entrypoints/options/index.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Options</title>
    <link rel="stylesheet" href="./style.css" />
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="./main.ts"></script>
  </body>
</html>
```

## 2. Build DOM nodes, set `textContent`

Never interpolate data into `innerHTML`: tab titles, URLs and page text are
attacker-controlled.

```typescript
// entrypoints/options/main.ts
import { settings, type Settings } from '@/utils/storage';

const app = document.querySelector<HTMLDivElement>('#app')!;
const label = document.createElement('label');
const checkbox = document.createElement('input');
checkbox.type = 'checkbox';
const text = document.createElement('span');
text.textContent = 'Enabled';
label.append(checkbox, text);
app.replaceChildren(label);

function render(current: Settings) {
  checkbox.checked = current.enabled;
}

checkbox.addEventListener('change', async () => {
  await settings.setValue({ ...(await settings.getValue()), enabled: checkbox.checked });
});

settings.watch(render);            // stays in sync with other surfaces
settings.getValue().then(render);
```

## 3. Structure as it grows

- One `render(state)` function per surface that updates existing nodes; event handlers
  write to storage or send a message, and the `watch` callback re-renders.
- Reusable pieces are functions returning elements (`createToggle(label, onChange)`)
  in `components/`.
- When a surface outgrows this (many views, lists with keyed updates), propose moving
  to a framework instead of writing a mini framework.

## 4. Injected UI

Content-script UI goes in `createShadowRootUi` with `onMount(container)` appending the
nodes and `onRemove` removing listeners (see `.claude/patterns/content-scripts.md`).

## 5. Don't

- `innerHTML` / `insertAdjacentHTML` with any data that is not a constant.
- Module-level timers in a popup: it is destroyed when it closes.
- `chrome.*` callbacks; use `browser` from `wxt/browser` and `await`.
