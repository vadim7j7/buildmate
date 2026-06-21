# Permissions

Permissions are declared in `wxt.config.ts` (WXT compiles them into the manifest).
Practice **least privilege**: every permission you request is shown to users at install
and reviewed by stores. Fewer, narrower permissions = faster review and more installs.

## 1. Declaring permissions

```typescript
// wxt.config.ts
import { defineConfig } from 'wxt';

export default defineConfig({
  manifest: {
    permissions: ['storage', 'activeTab', 'scripting'],
    host_permissions: ['*://*.example.com/*'],
    optional_permissions: ['bookmarks'],
    optional_host_permissions: ['*://*/*'],
  },
});
```

- `permissions` — API permissions (`storage`, `tabs`, `alarms`, `contextMenus`, …).
- `host_permissions` — sites the extension can read/modify or fetch cross-origin.
- `optional_*` — requested at runtime instead of install time (see §3).

## 2. Prefer activeTab + scripting over broad hosts

`activeTab` grants temporary access to the **current tab** when the user invokes the
extension (clicks the action / a context menu) — no scary "read data on all sites" prompt.

```typescript
// background — inject only into the tab the user just acted on
browser.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return;
  await browser.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => document.body.style.outline = '2px solid red',
  });
});
```

Use `host_permissions: ['<all_urls>']` only when the feature genuinely must run
everywhere automatically — expect extra store scrutiny.

## 3. Optional permissions + runtime request

Request rarely-used capabilities on demand, ideally from a user gesture:

```typescript
const granted = await browser.permissions.request({
  permissions: ['bookmarks'],
  origins: ['*://*.example.com/*'],
});
if (granted) { /* use it */ }

// check / remove later
await browser.permissions.contains({ permissions: ['bookmarks'] });
await browser.permissions.remove({ permissions: ['bookmarks'] });
```

## 4. MV3 scripting API

MV2's `tabs.executeScript` / `insertCSS` are gone. Use `browser.scripting`:

```typescript
await browser.scripting.executeScript({ target: { tabId }, files: ['/injected.js'] });
await browser.scripting.insertCSS({ target: { tabId }, css: 'body{filter:invert(1)}' });
```

Requires the `scripting` permission plus host access (or `activeTab`).

## 5. Content Security Policy

MV3 forbids remote code and inline scripts. You generally don't touch CSP, but if you
must adjust it (e.g. WASM), set it in the manifest:

```typescript
manifest: {
  content_security_policy: {
    extension_pages: "script-src 'self' 'wasm-unsafe-eval'; object-src 'self';",
  },
}
```

Never add remote origins to `script-src` — stores reject it. See `patterns/security.md`.

## 6. Audit regularly

Run the `permissions-audit` skill: it cross-checks declared permissions against actual
`browser.*` usage and flags anything unused or over-broad. Remove what you don't use.

## Checklist

- [ ] Only permissions actually used in code are declared
- [ ] `activeTab` + `scripting` preferred over broad `host_permissions`
- [ ] Rare capabilities are `optional_*` + requested from a user gesture
- [ ] No remote origins in `script-src`
- [ ] `npm run compile` after permission changes to regenerate the manifest
