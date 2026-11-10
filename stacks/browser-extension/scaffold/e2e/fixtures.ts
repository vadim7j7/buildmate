import path from 'node:path';
import { test as base, chromium, type BrowserContext } from '@playwright/test';

// Loads the built extension (`wxt build` -> .output/chrome-mv3) into Playwright's bundled
// Chromium. Branded Chrome ignores --load-extension, hence channel: 'chromium'.
// See .claude/patterns/testing.md (End-to-end with Playwright).
const pathToExtension = path.resolve('.output/chrome-mv3');

export const test = base.extend<{ context: BrowserContext; extensionId: string }>({
  // eslint-disable-next-line no-empty-pattern -- Playwright requires a destructured first arg
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
