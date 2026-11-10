# Testing Nuxt 4

Read this when writing or fixing tests. Tooling: Vitest + `@nuxt/test-utils`,
`@vue/test-utils`, `happy-dom`; Playwright for browser end-to-end.

## Layout and Config

Split tests by environment, so plain logic doesn't boot Nuxt:

```
tests/
  unit/   # pure TS (utils, Zod schemas, server/utils): node environment, fast
  nuxt/   # components, pages, composables, stores: Nuxt runtime environment
  e2e/    # boots the built app: server routes, full pages
```

```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import { defineVitestProject } from '@nuxt/test-utils/config';

export default defineConfig({
  test: {
    projects: [
      { test: { name: 'unit', include: ['tests/unit/**/*.test.ts'], environment: 'node' } },
      await defineVitestProject({
        test: {
          name: 'nuxt',
          include: ['tests/nuxt/**/*.test.ts'],
          environment: 'nuxt',
          environmentOptions: { nuxt: { domEnvironment: 'happy-dom' } },
        },
      }),
      { test: { name: 'e2e', include: ['tests/e2e/**/*.test.ts'], environment: 'node' } },
    ],
  },
});
```

A project with a single `defineVitestConfig({ test: { environment: 'nuxt' } })` works
too; follow what exists.

## Components and Pages (`tests/nuxt/`)

```ts
import { it, expect } from 'vitest';
import { mountSuspended, mockNuxtImport, registerEndpoint } from '@nuxt/test-utils/runtime';
import ProjectsPage from '~/pages/projects/index.vue';

registerEndpoint('/api/projects', () => [{ id: '1', name: 'Alpha' }]);

mockNuxtImport('useUserSession', () => () => ({
  loggedIn: ref(true),
  user: ref({ id: 'u1', email: 'a@example.com', role: 'member' }),
}));

it('lists projects', async () => {
  const wrapper = await mountSuspended(ProjectsPage, { route: '/projects' });
  expect(wrapper.text()).toContain('Alpha');
});
```

- `mountSuspended` (or `renderSuspended` with `@testing-library/vue`) runs setup with
  `await useFetch`, plugins and auto-imports. Plain `mount` does not.
- `registerEndpoint(path, handler | { method, handler, once })` fakes the API;
  `mockNuxtImport(name, factory)` replaces an auto-import (top level of the file);
  `mockComponent(name, factory)` stubs a heavy child.
- Query by role/label/text (`screen.getByRole('button', { name: 'Delete' })`) and
  interact with `@testing-library/user-event` or `await wrapper.find(...).trigger(...)`.

## Server Routes

Two levels:

- **Logic** in `server/utils/` (pure functions, Zod schemas): unit tests in `tests/unit/`.
- **Handlers**: e2e tests that boot the app.

```ts
// tests/e2e/projects.test.ts
import { describe, it, expect } from 'vitest';
import { setup, fetch } from '@nuxt/test-utils/e2e';

describe('projects API', async () => {
  await setup({ server: true });

  it('401 when signed out', async () => {
    expect((await fetch('/api/projects')).status).toBe(401);
  });

  it('400 on invalid body', async () => {
    const res = await fetch('/api/projects', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ name: '' }),
    });
    expect(res.status).toBe(400);
  });
});
```

Cover for each private route: signed out (401), someone else's record (404/403),
invalid input (400), happy path.

## Browser E2E (Playwright)

```ts
// tests/e2e/login.spec.ts
import { expect, test } from '@nuxt/test-utils/playwright';

test('signs in', async ({ page, goto }) => {
  await goto('/login', { waitUntil: 'hydration' });
  await page.getByLabel('Email').fill('a@example.com');
  await page.getByLabel('Password').fill('correct horse battery');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

Wait for hydration before interacting; clicks before hydration hit server HTML
without handlers and make tests flaky.

## Rules

- Test behaviour (rendered text, emitted events, requests made), not internals.
- No real network: `registerEndpoint` in nuxt tests, a test DB or fakes in e2e.
- Reset state between tests: `vi.restoreAllMocks()`, fresh Pinia per test.
- A bug fix comes with a test that fails before the fix.
