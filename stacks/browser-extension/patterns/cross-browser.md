# Cross-Browser Builds

WXT builds one codebase to Chrome, Edge, Firefox, and Safari. Most code is identical
because you use the unified `browser` API; the differences are handled with build-time
flags and per-browser manifest tweaks — never user-agent sniffing.

## 1. The unified `browser` API

Always import `browser` from `wxt/browser`. It is a promise-based WebExtension API that
behaves the same on Chromium and Gecko.

```typescript
import { browser } from 'wxt/browser';
const tabs = await browser.tabs.query({ active: true }); // works everywhere
```

WRONG: the raw `chrome.*` global is Chromium-only and callback-based.

## 2. Build-time environment flags

WXT injects compile-time constants. Dead-code elimination removes the unused branch per
target, so this is zero-cost:

```typescript
import.meta.env.BROWSER;           // 'chrome' | 'firefox' | 'edge' | 'safari'
import.meta.env.MANIFEST_VERSION;  // 2 | 3
import.meta.env.CHROME;            // boolean
import.meta.env.FIREFOX;           // boolean
import.meta.env.SAFARI;            // boolean

if (import.meta.env.FIREFOX) {
  // Gecko-specific path
}
if (import.meta.env.MANIFEST_VERSION === 3) {
  // MV3 path
}
```

## 3. Building each target

```bash
wxt build                # default target (chrome) → .output/chrome-mv3/
wxt build -b firefox     # → .output/firefox-mv2/ (or mv3)
wxt build -b edge
wxt zip                  # store-ready zip
wxt zip -b firefox       # Firefox zip + a sources zip (AMO requires source)
```

The scaffold wires these as `npm run build`, `build:firefox`, `zip`, `zip:firefox`.

## 4. Per-browser manifest overrides

Use the function form of `manifest` to branch on the active target:

```typescript
// wxt.config.ts
import { defineConfig } from 'wxt';

export default defineConfig({
  manifest: ({ browser, manifestVersion }) => ({
    name: 'My Extension',
    permissions: ['storage', 'activeTab'],
    // Firefox requires an explicit add-on id for some APIs
    ...(browser === 'firefox' && {
      browser_specific_settings: { gecko: { id: 'my-ext@example.com' } },
    }),
    // Chrome side panel vs Firefox sidebar are different manifest keys
    ...(browser === 'firefox'
      ? { sidebar_action: { default_panel: 'sidepanel.html' } }
      : {}),
  }),
});
```

## 5. MV2 vs MV3 differences WXT smooths over

- `action` (MV3) vs `browser_action` (MV2) — WXT maps these.
- Background: service worker (MV3) vs background scripts/pages (MV2).
- `host_permissions` separate from `permissions` in MV3.
- Firefox supports MV3 but with some Gecko-specific behaviours (event pages, not pure
  service workers in older versions). Test on Firefox, don't assume Chromium parity.

## 6. Safari

Safari uses WebKit and ships extensions inside a macOS/iOS app wrapper. Build the web
extension with WXT, then convert:

```bash
wxt build -b safari
xcrun safari-web-extension-converter .output/safari-mv3
```

Then open and sign the generated Xcode project. Some APIs (e.g. parts of
`declarativeNetRequest`, `scripting`) have Safari-specific limits — guard them with
`import.meta.env.SAFARI`.

## 7. Feature detection over assumptions

When an API may be missing on a target, check before calling:

```typescript
if ('sidePanel' in browser) {
  await browser.sidePanel.open({ windowId });
}
```

## Checklist

- [ ] Only the unified `browser` import is used; no raw `chrome.*`
- [ ] Browser/MV branches use `import.meta.env.*`, never UA strings
- [ ] Per-browser manifest differences handled via the `manifest` function form
- [ ] Firefox build includes a sources zip; Safari converted via `safari-web-extension-converter`
- [ ] Target-specific APIs feature-detected or guarded
