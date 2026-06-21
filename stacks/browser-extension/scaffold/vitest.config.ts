import { defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing';

// WxtVitest() polyfills import.meta.env, the unified `browser` global (fakeBrowser),
// and in-memory storage so extension code runs under Vitest. See patterns/testing.md
export default defineConfig({
  plugins: [WxtVitest()],
});
