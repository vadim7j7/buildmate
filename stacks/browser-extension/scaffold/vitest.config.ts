import { configDefaults, defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing/vitest-plugin';

// WxtVitest() polyfills import.meta.env, the unified `browser` global (fakeBrowser),
// and in-memory storage so extension code runs under Vitest. See .claude/patterns/testing.md
// e2e/ holds Playwright specs (npm run test:e2e), not Vitest tests.
export default defineConfig({
  plugins: [WxtVitest()],
  test: {
    exclude: [...configDefaults.exclude, 'e2e/**'],
  },
});
