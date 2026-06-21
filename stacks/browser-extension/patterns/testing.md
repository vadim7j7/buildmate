# Testing

Test extensions with **Vitest** + WXT's testing utilities. The `WxtVitest` plugin wires
up `import.meta.env`, the `browser` global, and in-memory storage, and
`@webext-core/fake-browser` provides a resettable fake of the WebExtension APIs.

## 1. Setup

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing';

export default defineConfig({
  plugins: [WxtVitest()],
});
```

Reset the fake browser between tests so state never leaks:

```typescript
import { fakeBrowser } from 'wxt/testing';
import { beforeEach } from 'vitest';

beforeEach(() => {
  fakeBrowser.reset(); // clears storage, listeners, mock tabs/windows
});
```

## 2. Test storage items

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { fakeBrowser } from 'wxt/testing';
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
import { storage } from 'wxt/storage';

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

## 7. End-to-end (optional)

For real-browser smoke tests, drive the built extension from `.output/` with Playwright's
persistent context (`launchPersistentContext` with `--load-extension`). Keep E2E thin;
prefer fast unit tests for logic.

## Checklist

- [ ] `WxtVitest()` configured; `fakeBrowser.reset()` in `beforeEach`
- [ ] Storage items, migrations, and message handlers covered
- [ ] Sender-validation guards tested for the reject case
- [ ] Content-script logic extracted to testable `utils/` functions
- [ ] `npm test` green before shipping
