# Testing

Test extensions with **Vitest** + WXT's testing utilities. The `WxtVitest` plugin wires
up `import.meta.env`, the `browser` global, and in-memory storage, and
`@webext-core/fake-browser` provides a resettable fake of the WebExtension APIs.

## 1. Setup

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing/vitest-plugin';

export default defineConfig({
  plugins: [WxtVitest()],
});
```

Reset the fake browser between tests so state never leaks:

```typescript
import { fakeBrowser } from 'wxt/testing/fake-browser';
import { beforeEach } from 'vitest';

beforeEach(() => {
  fakeBrowser.reset(); // clears storage, listeners, mock tabs/windows
});
```

## 2. Test storage items

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { fakeBrowser } from 'wxt/testing/fake-browser';
import { settings } from '@/utils/storage';

describe('settings', () => {
  beforeEach(() => fakeBrowser.reset());

  it('returns the fallback before anything is written', async () => {
    expect(await settings.getValue()).toEqual({ theme: 'light', enabled: true });
  });

  it('persists updates', async () => {
    await settings.setValue({ theme: 'dark', enabled: false });
    expect(await settings.getValue()).toEqual({ theme: 'dark', enabled: false });
  });
});
```

## 3. Test storage migrations

```typescript
import { storage } from 'wxt/utils/storage';

it('migrates v1 → v2', async () => {
  await storage.setItem('local:profile', { name: 'Ada', tag: 'admin' }); // v1 shape
  await storage.setMeta('local:profile', { v: 1 });
  expect(await profile.getValue()).toEqual({ name: 'Ada', tags: ['admin'] }); // v2
});
```

## 4. Test message handlers

Import the background entry to register handlers, then drive them via `sendMessage`, and
assert on both the response and storage side-effects. Cover the security guard:

```typescript
import { sendMessage } from '@/utils/messaging';

it('rejects messages from foreign senders', async () => {
  // configure fakeBrowser sender, then expect the handler to throw
  await expect(sendMessage('deleteAll', undefined)).rejects.toThrow('forbidden');
});
```

## 5. Test content-script logic

Extract pure DOM/transform logic into `utils/` functions and unit-test those directly —
no browser needed:

```typescript
import { extractPrice } from '@/utils/parse';

it('parses a price from product markup', () => {
  document.body.innerHTML = '<span class="price">$12.99</span>';
  expect(extractPrice(document)).toBe(12.99);
});
```

For DOM-dependent code, Vitest's `jsdom`/`happy-dom` environment or `@vitest/browser`
gives you `document`. Keep API calls behind the fake browser.

## 6. What to cover

- Every `ProtocolMap` method has a handler test (happy path + a rejected sender).
- Every `storage.defineItem` has fallback + round-trip + migration tests.
- Permission-gated paths assert the guard rejects when the permission is absent.
- Cross-browser branches (`import.meta.env.FIREFOX`, MV2/MV3) — exercise both sides.

## 7. End-to-end with Playwright (Chromium)

WXT recommends Playwright for E2E. It loads the **built** extension from
`.output/chrome-mv3` into a persistent Chromium context. Only Chromium works this way
(branded Chrome no longer honours `--load-extension`, so use Playwright's bundled
Chromium via `channel: 'chromium'`, which also runs headless). Firefox and Safari builds
are smoke-tested by hand.

```typescript
// e2e/fixtures.ts
import path from 'node:path';
import { test as base, chromium, type BrowserContext } from '@playwright/test';

const pathToExtension = path.resolve('.output/chrome-mv3');

export const test = base.extend<{ context: BrowserContext; extensionId: string }>({
  context: async ({}, use) => {
    const context = await chromium.launchPersistentContext('', {
      channel: 'chromium',
      args: [
        `--disable-extensions-except=${pathToExtension}`,
        `--load-extension=${pathToExtension}`,
      ],
    });
    await use(context);
    await context.close();
  },
  extensionId: async ({ context }, use) => {
    // MV3: the background is a service worker; its URL host is the extension id
    let [worker] = context.serviceWorkers();
    if (!worker) worker = await context.waitForEvent('serviceworker');
    await use(worker.url().split('/')[2]);
  },
});
export const expect = test.expect;
```

```typescript
// e2e/popup.spec.ts
import { test, expect } from './fixtures';

test('popup renders and toggles the theme', async ({ page, extensionId }) => {
  await page.goto(`chrome-extension://${extensionId}/popup.html`);
  const toggle = page.getByRole('button', { name: /Theme:/ });
  await expect(toggle).toHaveText('Theme: light');
  await toggle.click();
  await expect(toggle).toHaveText('Theme: dark');
});

test('content script runs on a matching page', async ({ page }) => {
  await page.goto('https://example.com');
  await expect(page.locator('my-overlay')).toBeAttached(); // the createShadowRootUi host
});
```

- `npm run test:e2e` = `wxt build && playwright test` (always test a fresh build).
- Install the browser once: `npx playwright install chromium`.
- Keep `e2e/` out of Vitest (`test.exclude` in `vitest.config.ts`).
- Surfaces open at `chrome-extension://<id>/<name>.html` (`popup.html`, `options.html`,
  `sidepanel.html`); the toolbar UI itself can't be clicked, so open the page directly.
- Keep E2E to a few smoke flows; logic belongs in fast unit tests.

## Checklist

- [ ] `WxtVitest()` configured; `fakeBrowser.reset()` in `beforeEach`
- [ ] Storage items, migrations, and message handlers covered
- [ ] Sender-validation guards tested for the reject case
- [ ] Content-script logic extracted to testable `utils/` functions
- [ ] A Playwright smoke spec loads the built extension (`npm run test:e2e`)
- [ ] `npm test` green before shipping
