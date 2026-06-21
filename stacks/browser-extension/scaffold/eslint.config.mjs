import js from '@eslint/js';
import tseslint from 'typescript-eslint';

// typescript-eslint disables core `no-undef`, so WXT's auto-imported globals
// (defineBackground, defineContentScript, etc.) don't trip the linter.
export default tseslint.config(
  { ignores: ['.output', '.wxt', 'node_modules'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    rules: {
      '@typescript-eslint/no-non-null-assertion': 'off',
    },
  },
);
