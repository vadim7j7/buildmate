# Logging in Express (pino)

Read this when adding logs, request logging, error reporting, or debugging production
issues. Use `pino` (structured JSON) and `pino-http` (one log line per request);
no `console.log` in application code.

## Logger

```typescript
// src/lib/logger.ts
import { randomUUID } from 'node:crypto';
import { pino } from 'pino';
import { pinoHttp } from 'pino-http';
import { env } from '@/lib/env';

export const logger = pino({
  level: env.LOG_LEVEL ?? (env.NODE_ENV === 'production' ? 'info' : 'debug'),
  redact: {
    paths: [
      'req.headers.authorization',
      'req.headers.cookie',
      'res.headers["set-cookie"]',
      '*.password',
      '*.token',
      '*.accessToken',
      '*.refreshToken',
    ],
    censor: '[redacted]',
  },
  // Pretty output only in development; production stays JSON for the log pipeline
  transport: env.NODE_ENV === 'development' ? { target: 'pino-pretty' } : undefined,
});

export const httpLogger = pinoHttp({
  logger,
  genReqId: (req, res) => {
    const id = req.headers['x-request-id']?.toString() ?? randomUUID();
    res.setHeader('x-request-id', id);
    return id;
  },
  customLogLevel: (_req, res, err) =>
    err || res.statusCode >= 500 ? 'error' : res.statusCode >= 400 ? 'warn' : 'info',
  autoLogging: { ignore: (req) => req.url === '/health' },
});
```

`app.use(httpLogger)` goes first in `src/app.ts`, so every request gets `req.log`
(a child logger carrying the request id).

## Writing Logs

```typescript
// object first, message second
req.log.info({ projectId: project.id }, 'Project created');
logger.warn({ userId, attempts }, 'Too many failed logins');
logger.error({ err }, 'Payment webhook failed'); // `err` key: pino serializes stack + cause
```

- Inside a request use `req.log` (has the request id); elsewhere (jobs, startup) `logger`
  or `logger.child({ job: 'sync-invoices' })`.
- Put data in fields, not in the message string (`{ orderId }`, not `` `order ${id}` ``),
  so logs can be filtered.
- Levels: `debug` dev detail · `info` business events · `warn` handled but unusual ·
  `error` failed operation needing attention · `fatal` process going down.

## Error Handler

```typescript
// unknown errors: log with the request id, answer generically
req.log.error({ err }, 'Unhandled error');
res.status(500).json({ error: 'Internal server error', requestId: req.id });
```

Expected errors (`AppError` 4xx, `ZodError`) are not logged at `error` level;
`pino-http` already logs the request at `warn`.

## Never Log

Passwords, tokens, API keys, session cookies, full card numbers, full request bodies
of auth endpoints, or personal data beyond an id. Add new sensitive paths to `redact`.

## Process-Level

Log `fatal` on `uncaughtException` / `unhandledRejection`, then shut down (see the
graceful shutdown section in `express-patterns.md`); pino flushes synchronously by
default, so the last line is not lost.

## Tests

Silence logs in tests: `LOG_LEVEL=silent` in the test env (pino accepts `'silent'`).
