# Tailwind CSS (Browser Extension)

This extension uses **Tailwind CSS v4** via the `@tailwindcss/vite` plugin, wired into
`wxt.config.ts`. UI surfaces (popup, options, side panel) get utility classes; content
scripts need one extra step (see §3).

## 1. How it's wired

`wxt.config.ts` registers the plugin:

```typescript
import { defineConfig } from 'wxt';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  vite: () => ({ plugins: [tailwindcss()] }),
  manifest: { /* ... */ },
});
```

Tailwind v4 is configured in CSS — there is **no `tailwind.config.js`** by default. A CSS
file imports the framework and you import that CSS from your entrypoint:

```css
/* entrypoints/popup/style.css */
@import "tailwindcss";
```

```typescript
// entrypoints/popup/main.ts (or main.tsx)
import './style.css';
```

## 2. Using utilities

```html
<div class="flex items-center gap-2 p-4">
  <h1 class="text-base font-semibold">My Extension</h1>
</div>
```

Customise the design system in CSS with `@theme`:

```css
@import "tailwindcss";

@theme {
  --color-brand: #4f46e5;
  --font-display: "Inter", sans-serif;
}
```

## 3. Content scripts: Tailwind inside a Shadow Root (important)

A content script's UI is mounted in a **shadow root** (`createShadowRootUi`) so page CSS
can't leak in. That isolation also means a normal `@import "tailwindcss"` on the page
won't style your shadow DOM. Bundle the CSS into the UI and let WXT inject it into the
shadow root with `cssInjectionMode: 'ui'`:

```typescript
// entrypoints/overlay.content.ts
import './overlay.css'; // contains @import "tailwindcss";

export default defineContentScript({
  matches: ['*://*.example.com/*'],
  cssInjectionMode: 'ui',           // inject styles into the shadow root, not the page
  async main(ctx) {
    const ui = await createShadowRootUi(ctx, {
      name: 'my-overlay',
      position: 'inline',
      onMount(container) {
        container.innerHTML = '<div class="rounded bg-brand p-3 text-white">Hi</div>';
      },
    });
    ui.mount();
  },
});
```

Tailwind's `rem`-based sizing keys off the host page's root font-size. For pixel-stable
overlays, scope a base font-size on your shadow container or prefer fixed units there.

## 4. Do / Don't

- ✅ One `@import "tailwindcss"` per CSS entry; import that CSS from the surface's main file.
- ✅ Use `@theme` for tokens instead of a JS config (v4 style).
- ✅ `cssInjectionMode: 'ui'` for any Tailwind used in a content-script shadow root.
- ❌ Don't expect page-level Tailwind to reach a shadow root.
- ❌ Don't add a CDN `<script src="cdn.tailwindcss.com">` — MV3 CSP forbids remote code
  (see `patterns/security.md`).

## Checklist

- [ ] `@tailwindcss/vite` plugin present in `wxt.config.ts`
- [ ] Each surface imports a CSS file that `@import "tailwindcss"`
- [ ] Content-script UIs use `cssInjectionMode: 'ui'` so utilities apply in the shadow root
- [ ] No remote Tailwind CDN; everything bundled at build time
