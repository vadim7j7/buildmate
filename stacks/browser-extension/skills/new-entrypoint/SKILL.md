---
name: new-entrypoint
description: Scaffold a new WXT entrypoint (popup, options, sidepanel, content script, background handler, or devtools)
---

# /new-entrypoint -- Scaffold a WXT Entrypoint

## What This Does

Creates a new entrypoint under `entrypoints/` following WXT conventions. WXT
auto-discovers everything in `entrypoints/` and generates the `manifest.json`
from it — you never hand-author the manifest. This skill picks the right file
shape for the chosen surface and registers any manifest keys it needs in
`wxt.config.ts`.

## Usage

```
/new-entrypoint popup                  # Action popup UI (entrypoints/popup/)
/new-entrypoint options                # Options page (entrypoints/options/)
/new-entrypoint sidepanel              # Side panel UI (entrypoints/sidepanel/)
/new-entrypoint content                # Content script (entrypoints/content.ts)
/new-entrypoint background             # Background service worker handler
/new-entrypoint devtools               # DevTools page (entrypoints/devtools/)
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `surface` | Yes | One of `popup`, `options`, `sidepanel`, `content`, `background`, `devtools` |
| `--vue` / `--react` | No | UI framework for HTML surfaces. Default: vanilla TS |

## How It Works

### 1. Determine the Entrypoint Shape

| Surface | Location | Shape |
|---|---|---|
| `popup` | `entrypoints/popup/` | `index.html` + `main.ts` |
| `options` | `entrypoints/options/` | `index.html` + `main.ts` |
| `sidepanel` | `entrypoints/sidepanel/` | `index.html` + `main.ts` |
| `devtools` | `entrypoints/devtools/` | `index.html` + `main.ts` |
| `content` | `entrypoints/content.ts` | `defineContentScript({...})` |
| `background` | `entrypoints/background.ts` | `defineBackground(() => {})` |

Use the `/new-content-script` skill for richer content scripts (matches, shadow
root UI). This skill creates the minimal valid version.

### 2. Generate the Files

**HTML surfaces (popup / options / sidepanel / devtools):**

```html
<!-- entrypoints/popup/index.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Popup</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="./main.ts"></script>
  </body>
</html>
```

```typescript
// entrypoints/popup/main.ts
import { browser } from 'wxt/browser';

const app = document.querySelector('#app');
if (app) {
  app.innerHTML = '<h1>Popup</h1>';
}
```

**Background:**

```typescript
// entrypoints/background.ts
export default defineBackground(() => {
  console.log('[ext] background started', { id: browser.runtime.id });
});
```

**Content (minimal — use /new-content-script for full version):**

```typescript
// entrypoints/content.ts
export default defineContentScript({
  matches: ['<all_urls>'],
  main(ctx) {
    console.log('[ext] content script injected');
  },
});
```

**DevTools** needs a panel-creation step:

```typescript
// entrypoints/devtools/main.ts
import { browser } from 'wxt/browser';

browser.devtools.panels.create('My Panel', '', 'panel.html');
```

### 3. Register Manifest Keys in `wxt.config.ts`

Most surfaces are auto-detected, but a few need manifest entries:

- **sidepanel** → add `"side_panel"` / `permissions: ['sidePanel']` (Chrome) and
  branch with `import.meta.env` for Firefox's `sidebar_action`.
- **devtools** → WXT auto-registers `devtools_page` from the entrypoint.
- **options** → WXT auto-registers `options_ui` from the entrypoint.

```typescript
// wxt.config.ts
import { defineConfig } from 'wxt';

export default defineConfig({
  manifest: {
    permissions: ['sidePanel'],
    // popup is wired via action automatically when entrypoints/popup exists
  },
});
```

### 4. Verify

```bash
npx wxt prepare && npx tsc --noEmit
npx wxt build            # confirm the generated manifest is valid
```

## Conventions

- UI surfaces are **directories** with `index.html` + `main.ts` — never a bare `.ts`.
- `background.ts` and `content.ts` are **single files** using the WXT helpers.
- Always `import { browser } from 'wxt/browser'` — never the `chrome` global.
- Keep entrypoints thin; put shared logic in `utils/` and `components/`.

## Checklist

- [ ] File(s) created in the correct `entrypoints/` location
- [ ] HTML surfaces have `index.html` + `main.ts` in their own directory
- [ ] `defineBackground` / `defineContentScript` used for background/content
- [ ] Required manifest keys added to `wxt.config.ts` (sidepanel permissions, etc.)
- [ ] `npx wxt prepare && tsc --noEmit` passes
- [ ] `npx wxt build` produces a valid manifest
