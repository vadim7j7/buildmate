---
name: new-test
description: Generate Vitest + Supertest tests for an Express endpoint, service or middleware
---

# /new-test

## What This Does

Writes tests for existing code: endpoint (integration, Supertest against `app` and
the test database), service (unit or DB-backed), or middleware. Covers the happy
path and the failure paths, then runs them.

## Usage

```
/new-test routes/projects             # src/routes/projects.test.ts (endpoint tests)
/new-test services/invite-service     # src/services/invite-service.test.ts
/new-test middleware/auth             # src/middleware/auth.test.ts
```

## How It Works

1. **Read** the code under test, its schema (`src/schemas/`), and existing tests;
   read `express-testing.md` if installed. If there is no `vitest.config.ts`, set it up
   as described there (alias `@`, node environment, test DB, `LOG_LEVEL=silent`).
2. **List the cases** before writing:

   | Kind | Cases |
   |---|---|
   | Endpoint | 401 without/with invalid token · 403 wrong role · 404 another user's record · 422 for each invalid input class (body, params, query) · happy path with response shape **and** DB side effect · pagination limits |
   | Service | each branch and error it throws · ownership scoping · edge values (empty, max length, unicode) |
   | Middleware | passes through (calls `next`) · rejects with the right status · doesn't touch `req.query` |

3. **Write** with explicit imports (`import { describe, it, expect } from 'vitest'`),
   `request(app)` from `supertest`, factories from `tests/helpers.ts` (create them if
   missing). Middleware can be tested through a tiny app:

   ```typescript
   const app = express();
   app.get('/admin', authenticate, requireRole('admin'), (_req, res) => res.sendStatus(204));
   app.use(errorHandler);

   it('403 for a member', async () => {
     const member = await createUser({ role: 'member' });
     await request(app).get('/admin').set(await authHeader(member)).expect(403);
   });
   ```

4. **Rules**: test behaviour through the public interface; real DB for endpoints (no
   Prisma mocks); mock only external services, clock and network (`vi.spyOn`,
   `vi.useFakeTimers()`); each test sets up its own data; no sleeps; for a bug, first
   a failing test that reproduces it.
5. **Run** `npm test` (or `npx vitest run <path>` while iterating). Report added
   tests, pass/fail counts, and failures with output. If a test exposes a bug in
   production code, report it; don't change the code to make the test pass.

## Generated Files

```
src/<path>.test.ts
tests/helpers.ts (if missing)
```
