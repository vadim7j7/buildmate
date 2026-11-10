# Testing Express (Vitest + Supertest)

Read this when writing or fixing tests, or setting up the test runner. Unit tests
for pure logic; integration tests that send real HTTP requests to `app` (no
`listen`) against a real test database.

## Setup

```bash
npm i -D vitest supertest @types/supertest @vitest/coverage-v8
npm pkg set scripts.test="vitest run"
```

```typescript
// vitest.config.ts
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }, // same as tsconfig paths
  },
  test: {
    environment: 'node',
    globalSetup: ['./tests/global-setup.ts'],
    setupFiles: ['./tests/setup.ts'],
    env: { NODE_ENV: 'test', LOG_LEVEL: 'silent' },
    fileParallelism: false, // integration tests share one test database
    restoreMocks: true,
  },
});
```

```typescript
// tests/global-setup.ts: once per run
import { execSync } from 'node:child_process';

export default function setup() {
  // DATABASE_URL must point at a disposable test DB (e.g. from .env.test / CI service)
  if (!process.env.DATABASE_URL?.includes('test')) {
    throw new Error('Refusing to run tests against a non-test DATABASE_URL');
  }
  execSync('npx prisma migrate deploy', { stdio: 'inherit' });
}
```

```typescript
// tests/setup.ts: before each test file
import { afterAll, beforeEach } from 'vitest';
import { prisma } from '@/lib/db';

// Child tables first. Table names are constants, never input.
const TABLES = ['"Project"', '"User"'];

beforeEach(async () => {
  await prisma.$executeRawUnsafe(`TRUNCATE ${TABLES.join(', ')} RESTART IDENTITY CASCADE`);
});

afterAll(async () => {
  await prisma.$disconnect();
});
```

## Factories and Auth Helpers

```typescript
// tests/helpers.ts
import { randomUUID } from 'node:crypto';
import { prisma } from '@/lib/db';
import { signAccessToken } from '@/lib/auth';

export async function createUser(overrides: Partial<{ email: string; role: 'admin' | 'member' }> = {}) {
  return prisma.user.create({
    data: { email: `${randomUUID()}@test.dev`, passwordHash: 'x', role: 'member', ...overrides },
  });
}

export async function authHeader(user: { id: string; role: 'admin' | 'member' }) {
  return { Authorization: `Bearer ${await signAccessToken(user)}` };
}
```

## Endpoint Tests

```typescript
// src/routes/projects.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import request from 'supertest';
import { app } from '@/app';
import { createUser, authHeader } from '../../tests/helpers';

describe('/projects', () => {
  let auth: Record<string, string>;
  let otherAuth: Record<string, string>;

  beforeEach(async () => {
    auth = await authHeader(await createUser());
    otherAuth = await authHeader(await createUser());
  });

  it('401 without a token', async () => {
    await request(app).get('/projects').expect(401);
  });

  it('422 on invalid body', async () => {
    const res = await request(app).post('/projects').set(auth).send({}).expect(422);
    expect(res.body.errors.name).toBeDefined();
  });

  it("404 for another user's project", async () => {
    const { body } = await request(app).post('/projects').set(auth).send({ name: 'Mine' }).expect(201);
    await request(app).get(`/projects/${body.id}`).set(otherAuth).expect(404);
  });

  it('creates and returns the project', async () => {
    const res = await request(app).post('/projects').set(auth).send({ name: 'Alpha' }).expect(201);
    expect(res.body).toMatchObject({ name: 'Alpha' });
    expect(res.body).not.toHaveProperty('ownerId'); // DTO, if the API hides it
  });
});
```

For every endpoint: 401, 403 (wrong role) / 404 (someone else's record), 422, happy
path, and the side effect in the DB (`prisma.project.count()`).

## Unit Tests and Mocks

```typescript
import { describe, it, expect, vi } from 'vitest';
import * as mailer from '@/lib/mailer';
import { InviteService } from '@/services/invite-service';

it('sends one invite email', async () => {
  const send = vi.spyOn(mailer, 'sendEmail').mockResolvedValue(undefined);
  await new InviteService().invite('a@test.dev');
  expect(send).toHaveBeenCalledOnce();
});
```

- Mock only the edges: email, payment, third-party HTTP (`vi.spyOn(globalThis, 'fetch')`),
  clock (`vi.useFakeTimers()`). Don't mock Prisma in endpoint tests: the real query
  (owner scoping, constraints) is what's being tested.
- `vi.mock('@/lib/x')` is hoisted; use it for whole-module fakes, `vi.spyOn` for one function.

## CI

Run a Postgres service, set `DATABASE_URL` to its test database, then `npm test`.
Coverage: `npx vitest run --coverage`.
