# Next.js Structured Logging Patterns

Structured logging patterns for Next.js applications.

---

## 1. Pino Logger Setup

### Installation

```bash
npm install pino pino-pretty
```

### Logger Configuration

```typescript
// lib/logger.ts
import pino from 'pino';

const isProduction = process.env.NODE_ENV === 'production';
const isServer = typeof window === 'undefined';

export const logger = pino({
  level: process.env.LOG_LEVEL || (isProduction ? 'info' : 'debug'),

  // Pretty print in development
  transport: !isProduction ? {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'SYS:standard',
      ignore: 'pid,hostname',
    },
  } : undefined,

  // Base fields for all logs
  base: {
    env: process.env.NODE_ENV,
    service: 'my-nextjs-app',
  },

  // Redact sensitive fields
  redact: {
    paths: ['password', 'token', 'authorization', 'cookie', '*.password', '*.token'],
    censor: '[REDACTED]',
  },

  // Format for production (JSON)
  formatters: isProduction ? {
    level: (label) => ({ level: label }),
  } : undefined,
});

// Create child loggers for different contexts
export const createLogger = (context: Record<string, unknown>) => {
  return logger.child(context);
};

// Browser-safe logger (no-op in browser unless explicitly enabled)
export const clientLogger = {
  info: (...args: unknown[]) => {
    if (process.env.NEXT_PUBLIC_ENABLE_CLIENT_LOGS === 'true') {
      console.log('[INFO]', ...args);
    }
  },
  warn: (...args: unknown[]) => console.warn('[WARN]', ...args),
  error: (...args: unknown[]) => console.error('[ERROR]', ...args),
};
```

---

## 2. API Route Logging

```typescript
// lib/api-logger.ts
import { NextRequest } from 'next/server';
import { createLogger } from './logger';

type LogContext = {
  method: string;
  path: string;
  requestId: string;
  userId?: string;
  duration?: number;
  status?: number;
};

export function createRequestLogger(request: NextRequest, userId?: string) {
  const requestId = request.headers.get('x-request-id') || crypto.randomUUID();

  return createLogger({
    component: 'api',
    method: request.method,
    path: request.nextUrl.pathname,
    requestId,
    userId,
  });
}

export function withLogging<T>(
  handler: (request: NextRequest, context: { logger: ReturnType<typeof createLogger> }) => Promise<T>
) {
  return async (request: NextRequest): Promise<T> => {
    const startTime = performance.now();
    const logger = createRequestLogger(request);

    logger.info('Request started');

    try {
      const result = await handler(request, { logger });
      const duration = Math.round(performance.now() - startTime);

      logger.info({ duration }, 'Request completed');
      return result;
    } catch (error) {
      const duration = Math.round(performance.now() - startTime);

      logger.error(
        {
          duration,
          error: error instanceof Error ? {
            name: error.name,
            message: error.message,
            stack: error.stack,
          } : error,
        },
        'Request failed'
      );

      throw error;
    }
  };
}

// Usage in API route
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { withLogging } from '@/lib/api-logger';

export const GET = withLogging(async (request, { logger }) => {
  logger.info('Fetching users');

  const users = await db.user.findMany();

  logger.info({ count: users.length }, 'Users fetched');

  return NextResponse.json(users);
});
```

---

## 3. Server Action Logging

```typescript
// lib/action-logger.ts
import { createLogger } from './logger';

type ActionResult<T> = { success: true; data: T } | { success: false; error: string };

export function withActionLogging<T, P extends unknown[]>(
  actionName: string,
  action: (...args: P) => Promise<T>
): (...args: P) => Promise<ActionResult<T>> {
  const logger = createLogger({ component: 'action', action: actionName });

  return async (...args: P): Promise<ActionResult<T>> => {
    const startTime = performance.now();

    logger.info({ args: sanitizeArgs(args) }, 'Action started');

    try {
      const result = await action(...args);
      const duration = Math.round(performance.now() - startTime);

      logger.info({ duration }, 'Action completed');

      return { success: true, data: result };
    } catch (error) {
      const duration = Math.round(performance.now() - startTime);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';

      logger.error(
        {
          duration,
          error: errorMessage,
        },
        'Action failed'
      );

      return { success: false, error: errorMessage };
    }
  };
}

function sanitizeArgs(args: unknown[]): unknown[] {
  return args.map((arg) => {
    if (typeof arg === 'object' && arg !== null) {
      const sanitized = { ...arg } as Record<string, unknown>;
      delete sanitized.password;
      delete sanitized.token;
      return sanitized;
    }
    return arg;
  });
}

// Usage
// app/actions/user.ts
'use server';

import { withActionLogging } from '@/lib/action-logger';

const createUserAction = async (data: CreateUserInput) => {
  // Implementation
  return user;
};

export const createUser = withActionLogging('createUser', createUserAction);
```

---

## 4. Middleware Logging

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { logger } from '@/lib/logger';

export function middleware(request: NextRequest) {
  const requestId = crypto.randomUUID();
  const startTime = Date.now();

  // Log incoming request
  logger.info({
    type: 'middleware',
    method: request.method,
    path: request.nextUrl.pathname,
    requestId,
    userAgent: request.headers.get('user-agent'),
    ip: request.ip || request.headers.get('x-forwarded-for'),
  }, 'Request received');

  const response = NextResponse.next();

  // Add request ID to response headers
  response.headers.set('x-request-id', requestId);

  // Log on response (note: this logs before the actual response completes)
  const duration = Date.now() - startTime;
  logger.info({
    type: 'middleware',
    method: request.method,
    path: request.nextUrl.pathname,
    requestId,
    duration,
  }, 'Request processed');

  return response;
}

export const config = {
  matcher: ['/api/:path*', '/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

---

## 5. Component Error Logging

```typescript
// components/ErrorBoundary.tsx
'use client';

import { Component, ReactNode } from 'react';
import { clientLogger } from '@/lib/logger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    clientLogger.error({
      component: 'ErrorBoundary',
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    });

    // Also send to server
    fetch('/api/log/error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        url: window.location.href,
        timestamp: new Date().toISOString(),
      }),
    }).catch(() => {
      // Ignore fetch errors
    });
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <DefaultErrorUI />;
    }

    return this.props.children;
  }
}

function DefaultErrorUI() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h2 className="text-xl font-semibold">Something went wrong</h2>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded"
        >
          Reload page
        </button>
      </div>
    </div>
  );
}
```

---

## 6. Database Query Logging

```typescript
// lib/db.ts
import { PrismaClient } from '@prisma/client';
import { createLogger } from './logger';

const logger = createLogger({ component: 'database' });

const prismaClientSingleton = () => {
  const prisma = new PrismaClient({
    log: [
      { emit: 'event', level: 'query' },
      { emit: 'event', level: 'error' },
      { emit: 'event', level: 'warn' },
    ],
  });

  // Log queries in development
  if (process.env.NODE_ENV === 'development') {
    prisma.$on('query', (e) => {
      logger.debug({
        query: e.query,
        params: e.params,
        duration: e.duration,
      }, 'Database query');
    });
  }

  // Always log slow queries
  prisma.$on('query', (e) => {
    if (e.duration > 100) {
      logger.warn({
        query: e.query,
        duration: e.duration,
      }, 'Slow query detected');
    }
  });

  prisma.$on('error', (e) => {
    logger.error({ error: e.message }, 'Database error');
  });

  return prisma;
};

export const db = prismaClientSingleton();
```

---

## 7. External API Logging

```typescript
// lib/api-client.ts
import { createLogger } from './logger';

const logger = createLogger({ component: 'external-api' });

type RequestConfig = {
  method?: string;
  headers?: Record<string, string>;
  body?: unknown;
};

export async function apiRequest<T>(
  url: string,
  config: RequestConfig = {}
): Promise<T> {
  const startTime = performance.now();
  const requestId = crypto.randomUUID();

  logger.info({
    requestId,
    method: config.method || 'GET',
    url,
  }, 'External API request started');

  try {
    const response = await fetch(url, {
      method: config.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
      body: config.body ? JSON.stringify(config.body) : undefined,
    });

    const duration = Math.round(performance.now() - startTime);

    if (!response.ok) {
      logger.error({
        requestId,
        status: response.status,
        duration,
      }, 'External API request failed');

      throw new Error(`API request failed: ${response.status}`);
    }

    const data = await response.json();

    logger.info({
      requestId,
      status: response.status,
      duration,
    }, 'External API request completed');

    return data as T;
  } catch (error) {
    const duration = Math.round(performance.now() - startTime);

    logger.error({
      requestId,
      duration,
      error: error instanceof Error ? error.message : 'Unknown error',
    }, 'External API request error');

    throw error;
  }
}
```

---

## 8. Log Aggregation Endpoint

```typescript
// app/api/log/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { logger } from '@/lib/logger';

export async function POST(request: NextRequest) {
  try {
    const logs = await request.json();

    // Process batch of client logs
    for (const log of Array.isArray(logs) ? logs : [logs]) {
      const level = log.level || 'info';
      const { level: _, ...data } = log;

      logger.child({ source: 'client' })[level](data, log.message || 'Client log');
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json(
      { error: 'Invalid log format' },
      { status: 400 }
    );
  }
}
```

---

## 9. Performance Logging

```typescript
// lib/performance-logger.ts
import { createLogger } from './logger';

const logger = createLogger({ component: 'performance' });

export function measureAsync<T>(
  name: string,
  fn: () => Promise<T>,
  metadata?: Record<string, unknown>
): Promise<T> {
  const startTime = performance.now();

  return fn()
    .then((result) => {
      const duration = Math.round(performance.now() - startTime);
      logger.info({ name, duration, ...metadata }, 'Operation completed');
      return result;
    })
    .catch((error) => {
      const duration = Math.round(performance.now() - startTime);
      logger.error({ name, duration, error: error.message, ...metadata }, 'Operation failed');
      throw error;
    });
}

// Usage
const users = await measureAsync(
  'fetchUsers',
  () => db.user.findMany({ where: { active: true } }),
  { filter: 'active' }
);
```

---

## 10. Structured Log Format

```typescript
// lib/log-format.ts
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface StructuredLog {
  timestamp: string;
  level: LogLevel;
  message: string;
  service: string;
  environment: string;
  requestId?: string;
  userId?: string;
  duration?: number;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
  metadata?: Record<string, unknown>;
}

export function formatLog(
  level: LogLevel,
  message: string,
  context: Partial<StructuredLog> = {}
): StructuredLog {
  return {
    timestamp: new Date().toISOString(),
    level,
    message,
    service: process.env.SERVICE_NAME || 'nextjs-app',
    environment: process.env.NODE_ENV || 'development',
    ...context,
  };
}
```
