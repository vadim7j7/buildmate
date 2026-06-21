# Content Scripts

Content scripts run in the context of web pages. WXT gives every content script a
`ctx` (`ContentScriptContext`) that you MUST use for timers, listeners, and UI so they
are torn down cleanly when the script is invalidated (SPA navigation, extension reload,
tab close).

## 1. Anatomy

```typescript
// entrypoints/example.content.ts
export default defineContentScript({
  matches: ['*://*.example.com/*'],
  runAt: 'document_idle',
  world: 'ISOLATED',
  main(ctx) {
    // your logic
  },
});
```

- `matches` — URL match patterns (required). Keep them as narrow as possible.
- `runAt` — `document_start` | `document_end` | `document_idle` (default).
- `world` — `ISOLATED` (default, separate JS context) or `MAIN` (the page's own context,
  can touch page globals but is untrusted).
- `cssInjectionMode` — `'manifest'` | `'ui'` | `'manual'` (see §4).

## 2. The ctx lifecycle (critical)

A content script can be **invalidated** while the page is still open. Bare timers and
listeners then leak or throw "Extension context invalidated". Always go through `ctx`:

WRONG:

```typescript
main() {
  setInterval(poll, 1000);                 // ❌ leaks after invalidation
  window.addEventListener('scroll', onScroll); // ❌ never removed
}
```

CORRECT:

```typescript
main(ctx) {
  ctx.setInterval(poll, 1000);                 // ✅ auto-cleared
  ctx.addEventListener(window, 'scroll', onScroll); // ✅ auto-removed

  ctx.onInvalidated(() => {
    // last-chance cleanup of anything ctx doesn't own
  });

  if (ctx.isValid) {
    // guard work that must not run on a dead context
  }
}
```

## 3. SPA navigation

Single-page apps change the URL without reloading, so your content script keeps running
across "pages". Listen for WXT's location-change event:

```typescript
main(ctx) {
  mountForRoute(location.pathname);
  ctx.addEventListener(window, 'wxt:locationchange', ({ newUrl }) => {
    mountForRoute(newUrl.pathname);
  });
}
```

## 4. Injecting UI into the page

Use `createShadowRootUi` to isolate your styles from the host page (and vice versa):

```typescript
export default defineContentScript({
  matches: ['*://*.example.com/*'],
  cssInjectionMode: 'ui', // bundle CSS into the shadow root
  async main(ctx) {
    const ui = await createShadowRootUi(ctx, {
      name: 'my-panel',
      position: 'inline',
      anchor: 'body',
      onMount(container) {
        const el = document.createElement('div');
        el.textContent = 'Hello from the extension';
        container.append(el);
      },
    });
    ui.mount();              // ui auto-removes when ctx is invalidated
  },
});
```

`createIntegratedUi` is the alternative when you want your element to inherit page styles
(no shadow root). For framework UIs, return/unmount the root in `onMount`/`onRemove`
(see `styles/ui-react.md`).

## 5. Isolated vs main world

- **ISOLATED** (default): your JS can read/modify the DOM but cannot see the page's JS
  variables. Safer; use this by default.
- **MAIN**: runs in the page context — needed to wrap page globals (e.g. patch `fetch`),
  but you have no access to extension APIs and the page can tamper with you. Communicate
  back to an ISOLATED script via `window.postMessage` and validate messages.

## 6. Talking to the rest of the extension

Content scripts can't call most privileged APIs. Send a typed message to the background
to do privileged work (`patterns/messaging.md`):

```typescript
import { sendMessage } from '@/utils/messaging';
main() {
  void sendMessage('trackVisit', { url: location.href });
}
```

## 7. Security with untrusted page content

The page is hostile. Never inject unsanitised page/user strings via `innerHTML`; never
`eval` page-provided code. See `patterns/security.md`.

## Checklist

- [ ] `matches` is as narrow as the feature allows
- [ ] All timers/listeners go through `ctx`; `ctx.onInvalidated` cleans up the rest
- [ ] SPA routes handled via `wxt:locationchange`
- [ ] Injected UI uses `createShadowRootUi` (or integrated UI deliberately)
- [ ] Privileged work delegated to the background via typed messaging
