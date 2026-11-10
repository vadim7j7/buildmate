import { defineConfig } from '@playwright/test';

// E2E against the built extension. Run with `npm run test:e2e` (builds first).
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // one persistent browser profile per test file
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
});
