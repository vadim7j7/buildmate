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

## 8. Formatting

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

## 9. ESLint and Prettier Enforcement

```bash
# Check
npm run lint
npx tsc --noEmit

# Fix
npm run lint -- --fix

# Format
npx prettier --write .
```

All code MUST pass `npm run lint` and `npx tsc --noEmit` before it can be committed.
