# Express Security

Read this when a task adds or changes routes, middleware, CORS, uploads, or anything
that takes user input. Auth itself: `express-auth.md`.

## Baseline Middleware (src/app.ts)

```typescript
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import { rateLimit } from 'express-rate-limit';
import { env } from '@/lib/env';

const app = express();

app.disable('x-powered-by');
app.set('trust proxy', env.TRUST_PROXY_HOPS); // e.g. 1 behind one load balancer; 0 locally
app.use(helmet());                             // secure headers (CSP, HSTS, nosniff, frameguard...)
app.use(
  cors({
    origin: env.CORS_ORIGINS,                  // explicit allow-list, e.g. ['https://app.example.com']
    credentials: true,                         // only if the frontend sends cookies
  }),
);
app.use(express.json({ limit: '100kb' }));     // cap body size
app.use(rateLimit({ windowMs: 60_000, limit: 300, standardHeaders: 'draft-8', legacyHeaders: false }));
```

- **CORS**: never `cors()` with no options in production (any origin). With
  `credentials: true` the origin must be an allow-list, never `*` or a reflected origin.
- **trust proxy**: set to the number of proxy hops (not `true`), or `req.ip` and the
  rate limiter can be spoofed through `X-Forwarded-For`.
- An API that only serves JSON can keep helmet's defaults; tighten CSP if it serves HTML.

## Rate Limiting

Strict limits on abuse-prone routes, on top of the global one:

```typescript
// src/middleware/rate-limit.ts
import { rateLimit } from 'express-rate-limit';

export const authLimiter = rateLimit({
  windowMs: 15 * 60_000,
  limit: 10,                         // 10 attempts per IP per 15 min
  standardHeaders: 'draft-8',
  legacyHeaders: false,
  skipSuccessfulRequests: true,      // count failures only
});

// src/routes/auth.ts
router.post('/login', authLimiter, validateBody(loginSchema), controller.login);
```

The default store is in memory (per process). With more than one instance, use a
shared store (e.g. `rate-limit-redis`) so limits hold across instances.

## Input and Output

- Validate **body, params and query** with Zod; services receive parsed values only.
- No mass assignment: write only schema fields to the DB (`prisma.user.update({ data: parsed })`),
  never `req.body` spread into `data`.
- Authorize every record: `where: { id, ownerId: req.user.id }` (IDOR).
- Map DB rows to response DTOs; never return password hashes, tokens, internal flags.
- Errors: generic message to the client, details to the log. The error handler
  never sends `err.stack` or `err.message` of unknown errors.

```typescript
const toUserDto = (u: User) => ({ id: u.id, email: u.email, name: u.name });
```

## Injection

- Prisma queries are parameterized. Raw SQL only as the tagged template
  ``prisma.$queryRaw`SELECT ... WHERE id = ${id}` ``; never `$queryRawUnsafe` /
  `$executeRawUnsafe` with user input.
- No `eval`, `new Function`, `child_process.exec` with input; use `execFile` with an
  argument array if a process must run.
- Paths from input: resolve and check they stay inside an allowed directory.

## Outbound Requests (SSRF)

Fetching a URL the user supplied can reach internal services and cloud metadata.
Allow-list hosts, reject private/link-local IPs after DNS resolution, set a timeout
(`fetch(url, { signal: AbortSignal.timeout(5000) })`), don't follow redirects blindly.

## File Uploads

`multer` with `limits: { fileSize }`, check the type from content (magic bytes), not
the extension; store outside the web root or in object storage with random names.

## Secrets and Config

- Read env once at startup and validate with Zod (`src/lib/env.ts`); crash early if missing.
- No secrets in code, logs, error responses or the repo; `.env` is git-ignored.
- `npm audit` / Dependabot for dependency CVEs; keep Express on 5.x.

## Checklist

- [ ] `helmet()`, explicit CORS allow-list, body size limit, `trust proxy` set correctly
- [ ] Rate limits on login, sign-up, password reset, OTP and contact routes
- [ ] Body, params and query validated; DB writes use parsed fields only
- [ ] Every record access scoped by owner/tenant
- [ ] DTOs in responses; no stack traces or internal messages to clients
- [ ] No unsafe raw SQL, shell or path handling with input
