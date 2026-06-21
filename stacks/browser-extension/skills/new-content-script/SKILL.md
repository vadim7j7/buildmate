---
name: new-content-script
description: Generate a WXT defineContentScript with matches, runAt, world, ctx-based lifecycle, and optional shadow-root UI
---

# /new-content-script -- Generate a WXT Content Script

## What This Does

Creates a content script entrypoint using `defineContentScript`. It wires the
injection options (`matches`, `runAt`, `world`), uses the `ctx`
(`ContentScriptContext`) for all timers and listeners so they tear down on
navigation, and optionally mounts an isolated UI via `createShadowRootUi`.

## Usage

```
/new-content-script gmail                          # matches all_urls, document_idle
/new-content-script pricewatch --match="*://*.amazon.com/*"
/new-content-script overlay --ui                   # with shadow-root UI mount
/new-content-script earlyhook --run-at=document_start
/new-content-script pagehook --world=MAIN          # run in the page's JS context
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Content script name (also the filename) |
| `--match` | No | URL match pattern. Default: `<all_urls>` |
| `--run-at` | No | `document_start` \| `document_end` \| `document_idle`. Default: `document_idle` |
| `--world` | No | `ISOLATED` (default) or `MAIN` (page's JS context) |
| `--ui` | No | Mount a Shadow DOM UI via `createShadowRootUi` |

## How It Works

### 1. Choose the Filename

A single content script can be `entrypoints/content.ts`. For multiple, use a
directory: `entrypoints/<name>.content.ts` or `entrypoints/<name>.content/index.ts`.

### 2. Generate the Content Script

```typescript
// entrypoints/pricewatch.content.ts
export default defineContentScript({
  matches: ['*://*.amazon.com/*'],
  runAt: 'document_idle',      // document_start | document_end | document_idle
  world: 'ISOLATED',           // ISOLATED (extension context) | MAIN (page context)

  main(ctx) {
    // Timers via ctx — auto-cleared when the context is invalidated
    ctx.setInterval(() => checkPrice(), 10_000);

    // Listeners via ctx — auto-removed on navigation / reload
    ctx.addEventListener(window, 'scroll', onScroll);

    // Resume-safe async: bail if the tab navigated during an await
    void run(ctx);

    // Explicit teardown hook
    ctx.onInvalidated(() => cleanup());
  },
});

async function run(ctx: ContentScriptContext) {
  const data = await loadData();
  if (!ctx.isValid) return;   // context died while awaiting
  render(data);
}
```

### 3. (Optional) Shadow-Root UI

With `--ui`, mount UI inside a Shadow DOM so the page's CSS can't bleed in and
the extension's styles stay isolated. Use `cssInjectionMode: 'ui'`.

```typescript
import './style.css';

export default defineContentScript({
  matches: ['*://*.example.com/*'],
  cssInjectionMode: 'ui',     // inject CSS into the shadow root, not the page

  async main(ctx) {
    const ui = await createShadowRootUi(ctx, {
      name: 'price-overlay',
      position: 'inline',
      anchor: 'body',
      onMount(container) {
        const badge = document.createElement('div');
        badge.textContent = 'Tracking price…';
        container.append(badge);
        return badge;        // returned value passed to onRemove
      },
      onRemove(badge) {
        badge?.remove();
      },
    });

    ui.mount();              // mount now; auto-removed on ctx invalidation
  },
});
```

### 4. Verify

```bash
npx wxt prepare && npx tsc --noEmit
npx wxt build
```

Then manually load the unpacked build and confirm the script injects only on the
intended pages and tears down cleanly on navigation (no "Extension context
invalidated" errors in the console).

## Conventions

- **Never** use bare `setInterval` / `setTimeout` / `addEventListener` — always `ctx.*`.
- Guard with `if (!ctx.isValid) return;` after every `await`.
- Scope `matches` as narrowly as possible (least privilege — avoid `<all_urls>`).
- Use `world: 'MAIN'` only when you must touch page globals; it has no extension API access.
- Always mount UI via `createShadowRootUi(ctx, ...)`; never append raw nodes to `document.body`.

## Checklist

- [ ] `defineContentScript` with explicit `matches`
- [ ] `runAt` / `world` set when non-default
- [ ] All timers/listeners go through `ctx`
- [ ] `ctx.isValid` guard after every `await`
- [ ] `ctx.onInvalidated` cleanup registered when holding resources
- [ ] Shadow-root UI used for any injected DOM (with `--ui`)
- [ ] `wxt prepare && tsc --noEmit` and `wxt build` pass
