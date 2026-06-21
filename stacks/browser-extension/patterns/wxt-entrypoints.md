# WXT Entrypoints

WXT builds the extension from the `entrypoints/` directory and **generates
`manifest.json` for you**. You never hand-write the manifest — you declare manifest
fields in `wxt.config.ts` and create entrypoint files; WXT wires them together per
browser target.

## 1. The entrypoints/ model

Every extension surface is a file or folder in `entrypoints/`. The filename determines
the surface type:

| File / folder | Surface | Export |
| --- | --- | --- |
| `background.ts` | Service worker (MV3) / background script (MV2) | `defineBackground(...)` |
| `content.ts` or `*.content.ts` | Content script | `defineContentScript(...)` |
| `*.content/index.ts` | Content script with its own folder (for CSS/assets) | `defineContentScript(...)` |
| `popup/index.html` | Toolbar popup | HTML + main module |
| `options/index.html` | Options page | HTML + main module |
| `sidepanel/index.html` | Side panel (Chrome) / sidebar (Firefox) | HTML + main module |
| `newtab/index.html` | New-tab override | HTML + main module |
| `devtools/index.html` | DevTools page | HTML + main module |
| `bookmarks/index.html`, `history/index.html` | Special-page overrides | HTML + main module |
| `*.sandbox.html` | Sandboxed page | HTML + main module |

WXT also auto-imports the `define*` helpers and the `browser` global, so you don't need
to import `defineBackground` / `defineContentScript`. (Importing `browser` from
`wxt/browser` explicitly is still encouraged for clarity — see `styles/extension.md`.)

## 2. Background

```typescript
// entrypoints/background.ts
import { browser } from 'wxt/browser';

export default defineBackground(() => {
  browser.runtime.onInstalled.addListener(() => {
    console.log('installed');
  });
});
```

Options form (control persistence / module type):

```typescript
export default defineBackground({
  persistent: false, // MV3 ignores this; affects MV2/Firefox
  type: 'module',
  main() {
    // ...
  },
});
```

See `patterns/background.md` for service-worker lifecycle rules.

## 3. Content scripts

```typescript
// entrypoints/example.content.ts
export default defineContentScript({
  matches: ['*://*.example.com/*'],
  runAt: 'document_idle',   // document_start | document_end | document_idle
  world: 'ISOLATED',        // or 'MAIN' to run in the page's JS context
  main(ctx) {
    // ctx (ContentScriptContext) handles cleanup — see patterns/content-scripts.md
  },
});
```

The `matches`, `runAt`, `world`, `cssInjectionMode`, etc. you set here are compiled into
the generated manifest's `content_scripts` entry. Multiple content scripts =
multiple `*.content.ts` files.

## 4. HTML UI surfaces

A UI surface is a folder with `index.html` plus a script module:

```
entrypoints/
  popup/
    index.html      # <script type="module" src="./main.ts"> (or main.tsx)
    main.ts
    style.css
```

WXT detects the folder name (`popup`, `options`, `sidepanel`, …) and adds the right
manifest key (`action.default_popup`, `options_ui.page`, `side_panel.default_path`, …).
See `patterns/ui-surfaces.md`.

## 5. Per-entrypoint manifest options

You can override manifest fields from inside an HTML entrypoint via `<meta>` tags WXT
understands, or set them globally in `wxt.config.ts`. For content scripts and the
background, the options object IS the manifest source.

```typescript
// wxt.config.ts
import { defineConfig } from 'wxt';

export default defineConfig({
  manifest: {
    name: 'My Extension',
    permissions: ['storage', 'activeTab'],
    action: { default_title: 'Open My Extension' },
  },
});
```

## 6. Assets vs public

- `public/` — copied verbatim to the build root. Reference with a root-absolute URL:
  `browser.runtime.getURL('/icon/128.png')`. Put extension icons here
  (`public/icon/16.png`, `/32.png`, `/48.png`, `/128.png`).
- `assets/` — processed by Vite (hashed, tree-shaken). Import these in code:
  `import logoUrl from '@/assets/logo.svg'`.

## 7. Path alias

WXT configures `@/` to point at the project root (the WXT `srcDir`). Use
`@/utils/...`, `@/components/...` everywhere instead of long relative paths.

## Checklist

- [ ] No hand-written `manifest.json` — everything flows from entrypoints + `wxt.config.ts`
- [ ] Each surface lives in its own correctly-named file/folder under `entrypoints/`
- [ ] Icons in `public/icon/`, processed assets in `assets/`
- [ ] `npm run compile` regenerates the manifest after entrypoint changes
