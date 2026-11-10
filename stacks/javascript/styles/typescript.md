# TypeScript Style Guide

Mandatory style rules for all TypeScript code in this project. These are enforced by
ESLint, Prettier, and by code review.

---

## 1. TypeScript Strict Mode

Enable strict mode in `tsconfig.json`. Never use `any` — use `unknown` with type guards.

```typescript
// GOOD
function processInput(input: unknown): string {
  if (typeof input === 'string') return input;
  if (typeof input === 'number') return String(input);
  throw new Error('Unexpected input type');
}

// BAD
function processInput(input: any): string {
  return input.toString();
}
```

---

## 2. `type` vs `interface`

Use `type` for all type definitions. Use `interface` only when extending third-party types.

```typescript
// GOOD
type UserProps = {
  name: string;
  email: string;
  role?: 'admin' | 'user';
};

// Use interface only for extending
interface CustomRequest extends Request {
  userId: string;
}
```

---

## 3. Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Types | `PascalCase` | `UserProps`, `ApiResponse` |
| Functions | `camelCase` | `getUserById`, `formatDate` |
| Variables | `camelCase` | `userName`, `isActive` |
| Constants | `SCREAMING_SNAKE` | `MAX_RETRIES`, `API_BASE_URL` |
| Files (modules) | `kebab-case` | `user-service.ts` |
| Files (types) | `kebab-case` | `user-types.ts` |
| Enums | `PascalCase` | `UserRole.Admin` |

---

## 4. Import Organization

Order imports in this sequence:

```typescript
// 1. Node built-ins
import { readFile } from 'node:fs/promises';

// 2. Third-party packages
import { z } from 'zod';

// 3. Internal absolute imports
import { db } from '@/lib/db';
import type { User } from '@/types/user';

// 4. Relative imports
import { formatDate } from '../utils';
import { UserCard } from './UserCard';
```

---

## 5. Named Exports

Always use named exports (not `export default`):

```typescript
// GOOD
export function createUser(input: CreateUserInput): Promise<User> { ... }
export class UserService { ... }

// BAD
export default function createUser(...) { ... }
```

---

## 6. Null and Undefined Handling

Use optional chaining and nullish coalescing:

```typescript
// GOOD
const name = user?.profile?.name ?? 'Anonymous';
const port = config.port ?? 3000;

// BAD
const name = user && user.profile && user.profile.name ? user.profile.name : 'Anonymous';
```

---

## 7. Async Patterns

Always handle errors in async code:

```typescript
// GOOD - explicit error handling
try {
  const data = await fetchData();
  return processData(data);
} catch (error) {
  if (error instanceof NotFoundError) {
    return null;
  }
  throw error;
}

// GOOD - Promise.all for parallel operations
const [users, projects] = await Promise.all([
  getUsers(),
  getProjects(),
]);
```

---

## 8. Runtime and Compiler Settings

Target **Node.js 24 LTS** (`"engines": { "node": ">=24" }` and an `.nvmrc` with `24`).
Libraries/services are ES modules (`"type": "module"`).

```jsonc
// tsconfig.json (Node service or library)
{
  "compilerOptions": {
    "target": "es2024",
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "verbatimModuleSyntax": true,   // `import type` for types; no import elision surprises
    "isolatedModules": true,
    "skipLibCheck": true,
    "outDir": "dist"
  }
}
```

Frameworks with their own bundler (Next.js, Nuxt, Vite) ship their own `module` /
`moduleResolution` settings; keep those.

---

## 9. Formatting

Configure Prettier:

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 100
}
```

---

## 10. ESLint (flat config)

ESLint 9+ reads only `eslint.config.*` (flat config); `.eslintrc*` files are ignored.

```js
// eslint.config.js
import js from '@eslint/js';
import { defineConfig } from 'eslint/config';
import tseslint from 'typescript-eslint';
import prettier from 'eslint-config-prettier/flat';

export default defineConfig(
  { ignores: ['dist/', 'coverage/', '**/generated/'] },
  js.configs.recommended,
  tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    rules: {
      '@typescript-eslint/consistent-type-definitions': ['error', 'type'],
      '@typescript-eslint/no-floating-promises': 'error',
    },
  },
  prettier, // last: turns off rules that fight Prettier
);
```

Framework stacks extend this with their own preset (`eslint-config-next`, `@nuxt/eslint`).

---

## 11. Tests (Vitest defaults)

```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
    restoreMocks: true,                 // undo vi.spyOn / vi.fn implementations after each test
    coverage: { provider: 'v8', include: ['src/**'] },
  },
});
```

- `"test": "vitest run"` in `package.json` (CI), `vitest` for watch mode.
- Tests import `describe`/`it`/`expect`/`vi` from `vitest` explicitly (no globals).
- Details: `.claude/patterns/js-testing.md`.

---

## 12. Enforcement

```bash
# Check
npm run lint
npx tsc --noEmit
npm test

# Fix
npm run lint -- --fix
npx prettier --write .
```

All code MUST pass `npm run lint`, `npx tsc --noEmit` and `npm test` before it can be committed.
