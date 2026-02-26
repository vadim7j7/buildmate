# TypeScript Code Patterns

Reference patterns for generic TypeScript development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Module Organization

Organize code into well-defined modules with clear exports.

```typescript
// src/services/user-service.ts
import type { User, CreateUserInput } from '@/types/user';
import { db } from '@/lib/db';

export class UserService {
  async list(options: { skip?: number; limit?: number } = {}): Promise<User[]> {
    const { skip = 0, limit = 20 } = options;
    return db.user.findMany({ skip, take: limit });
  }

  async getById(id: string): Promise<User | null> {
    return db.user.findUnique({ where: { id } });
  }

  async create(input: CreateUserInput): Promise<User> {
    return db.user.create({ data: input });
  }

  async update(id: string, input: Partial<CreateUserInput>): Promise<User> {
    return db.user.update({ where: { id }, data: input });
  }

  async delete(id: string): Promise<void> {
    await db.user.delete({ where: { id } });
  }
}
```

### Rules

- One class or set of related functions per file
- Use `type` imports for type-only imports
- Export from barrel files (`index.ts`) for public APIs
- Keep files under 300 lines

---

## 2. Async/Await Patterns

Always use async/await for asynchronous operations.

```typescript
// GOOD - async/await
async function fetchData(url: string): Promise<Data> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new AppError(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<Data>;
}

// GOOD - parallel execution
async function loadDashboard(userId: string): Promise<Dashboard> {
  const [user, projects, notifications] = await Promise.all([
    userService.getById(userId),
    projectService.listByUser(userId),
    notificationService.getUnread(userId),
  ]);

  return { user, projects, notifications };
}

// GOOD - error handling with specific types
async function safeOperation<T>(fn: () => Promise<T>): Promise<T | null> {
  try {
    return await fn();
  } catch (error) {
    if (error instanceof AppError) {
      logger.error(error.message, { code: error.code });
    }
    return null;
  }
}
```

---

## 3. Error Handling

Use typed error classes for domain-specific errors.

```typescript
// src/lib/errors.ts
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string = 'INTERNAL_ERROR',
    public readonly statusCode: number = 500,
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} not found: ${id}`, 'NOT_FOUND', 404);
    this.name = 'NotFoundError';
  }
}

export class ValidationError extends AppError {
  constructor(
    message: string,
    public readonly errors: Record<string, string[]> = {},
  ) {
    super(message, 'VALIDATION_ERROR', 422);
    this.name = 'ValidationError';
  }
}
```

---

## 4. Configuration

Environment-based configuration with type safety.

```typescript
// src/lib/config.ts
import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string(),
  REDIS_URL: z.string().optional(),
});

export const config = envSchema.parse(process.env);
export type Config = z.infer<typeof envSchema>;
```

---

## 5. Logging

Structured logging with context.

```typescript
// src/lib/logger.ts
export const logger = {
  info(message: string, context?: Record<string, unknown>) {
    console.log(JSON.stringify({ level: 'info', message, ...context, timestamp: new Date().toISOString() }));
  },
  error(message: string, context?: Record<string, unknown>) {
    console.error(JSON.stringify({ level: 'error', message, ...context, timestamp: new Date().toISOString() }));
  },
  warn(message: string, context?: Record<string, unknown>) {
    console.warn(JSON.stringify({ level: 'warn', message, ...context, timestamp: new Date().toISOString() }));
  },
};
```

---

## 6. Test Patterns

```typescript
// src/services/__tests__/user-service.test.ts
import { UserService } from '../user-service';
import { db } from '@/lib/db';

describe('UserService', () => {
  const service = new UserService();

  describe('list', () => {
    it('returns paginated users', async () => {
      const users = await service.list({ skip: 0, limit: 10 });
      expect(users).toBeInstanceOf(Array);
    });

    it('uses default pagination', async () => {
      const users = await service.list();
      expect(users.length).toBeLessThanOrEqual(20);
    });
  });

  describe('getById', () => {
    it('returns null for non-existent user', async () => {
      const user = await service.getById('non-existent');
      expect(user).toBeNull();
    });
  });

  describe('create', () => {
    it('creates a user with valid input', async () => {
      const user = await service.create({ name: 'Test', email: 'test@example.com' });
      expect(user.id).toBeDefined();
      expect(user.name).toBe('Test');
    });
  });
});
```
