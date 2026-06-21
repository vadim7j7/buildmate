# Browser Extension Style Guide

Style conventions for all WXT browser extension code. The extension targets
Chrome, Firefox, Edge, and Safari from a single codebase using WXT
(https://wxt.dev), TypeScript strict mode, Manifest V3, and Vitest. All agents
must follow these conventions when generating or modifying code. They are
enforced by TypeScript strict mode, ESLint, and code review.

---

## 1. Project Structure

WXT discovers entrypoints by convention. Keep the file layout below; never
hand-author a `manifest.json` (WXT generates it from `wxt.config.ts` and the
entrypoints).

```
my-extension/
├── entrypoints/          # WXT auto-discovers these (background, content, UI)
│   ├── background.ts
│   ├── content.ts
│   ├── popup/            # index.html + main.ts/tsx
│   ├── options/          # index.html + main.ts/tsx
│   └── sidepanel/        # index.html + main.ts/tsx
├── components/           # Reusable UI components (shared across surfaces)
├── utils/                # Pure helpers, messaging protocol, storage items
├── assets/               # Bundled assets (imported, hashed by Vite)
├── public/               # Copied verbatim (icons, _locales, static files)
├── wxt.config.ts         # defineConfig — manifest + modules live here
├── tsconfig.json         # Extends .wxt/tsconfig.json
└── package.json
```

```typescript
// CORRECT — entrypoints live under entrypoints/ with WXT helpers
// entrypoints/background.ts
export default defineBackground(() => {
  // ...
});

// WRONG — hand-written manifest.json + raw script files
// manifest.json  { "background": { "service_worker": "bg.js" } }
```

Rules:
- One concern per file under `utils/`: `utils/messaging.ts`, `utils/storage.ts`.
- Assets that need hashing/bundling go in `assets/` and are **imported**.
- Static files served by URL (icons, `_locales/`) go in `public/`.
- Never edit the generated `.output/` or `.wxt/` directories.

---

## 2. TypeScript Strict Conventions

TypeScript strict mode is enabled (via the generated `.wxt/tsconfig.json`).

```typescript
// No `any` — use `unknown` and narrow
// CORRECT
function parseMessage(raw: unknown): Message {
  if (typeof raw === 'object' && raw !== null && 'type' in raw) {
    return raw as Message;
  }
  throw new Error('Invalid message');
}

// WRONG
function parseMessage(raw: any): Message {
  return raw;
}

// No non-null assertions — use optional chaining + nullish coalescing
// CORRECT
const activeTab = tabs[0]?.id ?? null;

// WRONG
const activeTab = tabs[0]!.id;
```

Rules:
- No `any` — use `unknown` and type guards.
- No `!` non-null assertions — use optional chaining and `??`.
- No unsafe `as` casts except at validated boundaries (parsed messages, storage).
- Export interfaces/types that cross entrypoint boundaries.
- Prefer discriminated unions for message and state variants.

---

## 3. Always Import `browser` from `wxt/browser`

WXT provides a unified, promise-based, cross-browser API. **Never** touch the
raw `chrome.*` or `browser.*` globals — they differ between Chrome (callback
`chrome`) and Firefox (`browser`), and the global is untyped under WXT.

```typescript
// CORRECT
import { browser } from 'wxt/browser';

const tabs = await browser.tabs.query({ active: true, currentWindow: true });
await browser.action.setBadgeText({ text: '3' });

// WRONG — raw chrome global, callback-based, Chrome-only
chrome.storage.local.get('key', (result) => { /* ... */ });

// WRONG — relying on the ambient browser global
const tabs = await tabs.query({ active: true });
```

Rules:
- Always `import { browser } from 'wxt/browser'`.
- Never reference the bare `chrome` global, even in Chrome-only code paths.
- The `browser` API is always promise-based — use `await`, never callbacks.

---

## 4. Use `wxt/storage` `defineItem` over Raw Storage

Never call `browser.storage.local.get/set` directly in feature code. Define a
typed storage item once in `utils/storage.ts` and import it. This gives you
type safety, defaults, versioning/migrations, and change watching.

```typescript
// CORRECT — utils/storage.ts
import { storage } from 'wxt/storage';

export interface Settings {
  theme: 'light' | 'dark';
  enabled: boolean;
}

export const settings = storage.defineItem<Settings>('local:settings', {
  fallback: { theme: 'light', enabled: true },
});

// usage anywhere
import { settings } from '@/utils/storage';
const current = await settings.getValue();   // fully typed, never undefined
await settings.setValue({ ...current, enabled: false });

// WRONG — raw, untyped, no default
const result = await browser.storage.local.get('settings');
const enabled = result.settings?.enabled;
```

Rules:
- Always namespace the key with an area: `'local:'`, `'sync:'`, `'session:'`.
- Provide a `fallback` so `getValue()` is never `undefined`.
- Add `version` + `migrations` when the shape evolves (see `/new-storage-item`).
- Subscribe to changes with `item.watch(cb)` instead of `browser.storage.onChanged`.

---

## 5. Content Scripts Must Use `ctx`

Content scripts receive a `ctx` (`ContentScriptContext`) in `main(ctx)`. The
context is invalidated when the script's tab navigates or the extension
reloads. **Always** register timers and listeners through `ctx` so they are
torn down automatically — a bare `setInterval` or `addEventListener` leaks and
throws "Extension context invalidated" errors.

```typescript
// CORRECT
export default defineContentScript({
  matches: ['*://*.example.com/*'],
  main(ctx) {
    // auto-cleared on invalidation
    ctx.setInterval(() => poll(), 5000);

    // auto-removed on invalidation
    ctx.addEventListener(window, 'scroll', onScroll);

    // guard async work that resumes after an await
    ctx.onInvalidated(() => teardown());
  },
});

// WRONG — bare timer/listener, leaks after navigation
export default defineContentScript({
  matches: ['*://*.example.com/*'],
  main() {
    setInterval(() => poll(), 5000);
    window.addEventListener('scroll', onScroll);
  },
});
```

Rules:
- Use `ctx.setInterval` / `ctx.setTimeout` over the globals.
- Use `ctx.addEventListener(target, type, handler)` for DOM listeners.
- Check `ctx.isValid` before touching the DOM after an `await`.
- Mount UI via `createShadowRootUi(ctx, ...)` and store the returned handle.

---

## 6. No Remote Code / Inline Scripts (MV3 CSP)

Manifest V3 forbids remote code execution and inline scripts. Everything must be
bundled at build time. WXT enforces this, but write code that respects it.

```typescript
// CORRECT — bundle the dependency, import it
import { z } from 'zod';
const schema = z.object({ id: z.string() });

// WRONG — loading a remote script at runtime
const script = document.createElement('script');
script.src = 'https://cdn.example.com/lib.js'; // blocked by MV3 CSP

// WRONG — eval / new Function on remote or dynamic strings
eval(downloadedCode);
```

Rules:
- No `<script src="https://...">` injected at runtime; no remote `import()` of URLs.
- No `eval`, `new Function`, or string-based timers.
- No inline event handlers (`onclick="..."`) in HTML — attach listeners in JS.
- Bundle every dependency; fetch **data** over the network, never executable code.

---

## 7. Typed Message Handlers

All cross-context messaging goes through `@webext-core/messaging`. Define one
`ProtocolMap` so callers and handlers are fully typed; never call
`browser.runtime.sendMessage` with untyped payloads.

```typescript
// CORRECT — utils/messaging.ts
import { defineExtensionMessaging } from '@webext-core/messaging';

interface ProtocolMap {
  getTabTitle(): string;
  saveBookmark(data: { url: string; title: string }): boolean;
}

export const { sendMessage, onMessage } =
  defineExtensionMessaging<ProtocolMap>();

// background handler — return type checked against ProtocolMap
onMessage('saveBookmark', async ({ data }) => {
  await persist(data);
  return true;
});

// caller — args + return type inferred
const ok = await sendMessage('saveBookmark', { url, title });

// WRONG — untyped, stringly-typed message envelope
browser.runtime.sendMessage({ action: 'saveBookmark', url, title });
```

Rules:
- One `ProtocolMap` per extension, declared in `utils/messaging.ts`.
- Handlers live in the background entrypoint; register them at top level.
- Never dispatch on a `type`/`action` string with manual `switch` handling.

---

## 8. Error Handling

Extension APIs reject promises; the DOM in content scripts can disappear
mid-task. Handle failure explicitly and never swallow errors silently.

```typescript
// CORRECT
async function getActiveTab(): Promise<Tab | null> {
  try {
    const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
    return tab ?? null;
  } catch (error) {
    console.error('[ext] tabs.query failed', error);
    return null;
  }
}

// CORRECT — bail out if the content script context died after an await
async function annotate(ctx: ContentScriptContext) {
  const data = await sendMessage('getData', undefined);
  if (!ctx.isValid) return;
  render(data);
}

// WRONG — unhandled rejection, no context guard
async function annotate() {
  const data = await sendMessage('getData', undefined);
  render(data); // may throw if the tab navigated
}
```

Rules:
- Wrap `browser.*` and `sendMessage` calls in try/catch at the boundary.
- Type caught errors as `unknown`; narrow before reading `.message`.
- Guard with `ctx.isValid` after every `await` inside content scripts.
- Surface user-facing failures in the UI; log internal ones with a tag prefix.

---

## 9. When to Branch on `import.meta.env.BROWSER`

WXT injects build-time constants. Prefer feature detection; only branch on the
target browser for genuine, known API differences. These are statically
replaced at build time, so dead branches are tree-shaken out.

```typescript
// CORRECT — known API difference (Firefox lacks chrome.action on MV2-style)
import { browser } from 'wxt/browser';

if (import.meta.env.FIREFOX) {
  await browser.browserAction.setBadgeText({ text });
} else {
  await browser.action.setBadgeText({ text });
}

// CORRECT — manifest-version aware logic
if (import.meta.env.MANIFEST_VERSION === 3) {
  // service worker path
}

// WRONG — runtime UA sniffing for something WXT resolves at build time
if (navigator.userAgent.includes('Firefox')) { /* ... */ }
```

Available build-time constants:

| Constant | Type | Meaning |
|---|---|---|
| `import.meta.env.BROWSER` | string | Target: `'chrome'`, `'firefox'`, `'edge'`, `'safari'` |
| `import.meta.env.CHROME` | boolean | True when building for Chrome |
| `import.meta.env.FIREFOX` | boolean | True when building for Firefox |
| `import.meta.env.SAFARI` | boolean | True when building for Safari |
| `import.meta.env.EDGE` | boolean | True when building for Edge |
| `import.meta.env.MANIFEST_VERSION` | 2 \| 3 | Target manifest version |
| `import.meta.env.MODE` | string | `'development'` or `'production'` |

Rules:
- Branch only for real API differences, not styling or behaviour preferences.
- Use the boolean flags (`import.meta.env.FIREFOX`) for tree-shakable branches.
- Never UA-sniff at runtime for things resolvable at build time.

---

## 10. Naming Conventions

| Entity | Convention | Example |
|---|---|---|
| Entrypoint file | lowercase | `background.ts`, `content.ts` |
| UI entrypoint dir | lowercase | `popup/`, `options/`, `sidepanel/` |
| Component | PascalCase | `BookmarkList`, `SettingsForm` |
| Component file | PascalCase | `BookmarkList.tsx` |
| Storage item | camelCase noun | `settings`, `recentTabs` |
| Storage key | `area:key` | `'local:settings'`, `'sync:theme'` |
| Message name | camelCase verb | `saveBookmark`, `getTabTitle` |
| Util module | camelCase | `messaging.ts`, `storage.ts` |
| Test file | `*.test.ts` | `messaging.test.ts` |
| Match pattern | URL match pattern | `'*://*.example.com/*'` |

---

## 11. Vitest and Type Enforcement

WXT ships a Vitest config preset (`WxtVitest`) that mocks `wxt/browser`,
`wxt/storage`, and the build-time env. Run these before code is complete:

```bash
# Type check (uses the generated .wxt/tsconfig.json)
npx wxt prepare && npx tsc --noEmit

# Tests
npx vitest run

# Build all targets to confirm the manifest is valid
npx wxt build && npx wxt build -b firefox
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing';

export default defineConfig({
  plugins: [WxtVitest()],
});
```

Rules:
- Use `WxtVitest()` so `browser`, `storage`, and `import.meta.env` are mocked.
- `fakeBrowser.reset()` between tests when asserting on extension APIs.
- TypeScript check, tests, and both browser builds must pass with zero errors
  before code is considered complete.
