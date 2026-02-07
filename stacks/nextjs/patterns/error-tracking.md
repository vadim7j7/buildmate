# Next.js Error Tracking Patterns

Error tracking patterns using Sentry for Next.js applications.

---

## 1. Sentry Setup

### Installation

```bash
npx @sentry/wizard@latest -i nextjs
```

### Configuration

```typescript
// sentry.client.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  release: process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA,

  // Performance monitoring
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

  // Session replay
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,

  integrations: [
    Sentry.replayIntegration({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],

  // Filter out noisy errors
  beforeSend(event, hint) {
    const error = hint.originalException as Error;

    // Ignore cancelled requests
    if (error?.name === 'AbortError') {
      return null;
    }

    // Ignore network errors from third-party scripts
    if (error?.message?.includes('Script error')) {
      return null;
    }

    return event;
  },
});
```

```typescript
// sentry.server.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  release: process.env.VERCEL_GIT_COMMIT_SHA,

  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

  // Capture unhandled promise rejections
  integrations: [
    Sentry.captureConsoleIntegration({ levels: ['error'] }),
  ],
});
```

```typescript
// sentry.edge.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1,
});
```

---

## 2. Next.js Configuration

```javascript
// next.config.js
const { withSentryConfig } = require('@sentry/nextjs');

const nextConfig = {
  // Your existing config
};

module.exports = withSentryConfig(nextConfig, {
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  authToken: process.env.SENTRY_AUTH_TOKEN,

  silent: true,
  widenClientFileUpload: true,
  hideSourceMaps: true,
  disableLogger: true,
});
```

---

## 3. Error Boundary with Sentry

```typescript
// components/SentryErrorBoundary.tsx
'use client';

import * as Sentry from '@sentry/nextjs';
import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode | ((error: Error, resetError: () => void) => ReactNode);
}

interface State {
  hasError: boolean;
  error: Error | null;
  eventId: string | null;
}

export class SentryErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, eventId: null };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    Sentry.withScope((scope) => {
      scope.setExtra('componentStack', errorInfo.componentStack);
      const eventId = Sentry.captureException(error);
      this.setState({ eventId });
    });
  }

  resetError = () => {
    this.setState({ hasError: false, error: null, eventId: null });
  };

  render() {
    if (this.state.hasError) {
      if (typeof this.props.fallback === 'function') {
        return this.props.fallback(this.state.error!, this.resetError);
      }

      return this.props.fallback || (
        <ErrorFallback
          error={this.state.error!}
          eventId={this.state.eventId}
          resetError={this.resetError}
        />
      );
    }

    return this.props.children;
  }
}

function ErrorFallback({
  error,
  eventId,
  resetError,
}: {
  error: Error;
  eventId: string | null;
  resetError: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
      <h2 className="text-2xl font-bold mb-4">Something went wrong</h2>
      <p className="text-gray-600 mb-4">{error.message}</p>

      <div className="flex gap-4">
        <button
          onClick={resetError}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Try again
        </button>

        {eventId && (
          <button
            onClick={() => Sentry.showReportDialog({ eventId })}
            className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
          >
            Report feedback
          </button>
        )}
      </div>
    </div>
  );
}
```

---

## 4. Global Error Handler

```typescript
// app/global-error.tsx
'use client';

import * as Sentry from '@sentry/nextjs';
import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html>
      <body>
        <div className="flex flex-col items-center justify-center min-h-screen">
          <h2 className="text-2xl font-bold mb-4">Something went wrong!</h2>
          <button
            onClick={reset}
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
```

```typescript
// app/error.tsx
'use client';

import * as Sentry from '@sentry/nextjs';
import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px]">
      <h2 className="text-xl font-semibold mb-4">Something went wrong!</h2>
      <button
        onClick={reset}
        className="px-4 py-2 bg-blue-500 text-white rounded"
      >
        Try again
      </button>
    </div>
  );
}
```

---

## 5. API Route Error Handling

```typescript
// lib/api-error-handler.ts
import * as Sentry from '@sentry/nextjs';
import { NextRequest, NextResponse } from 'next/server';

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code: string = 'INTERNAL_ERROR',
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export function withErrorHandler<T>(
  handler: (request: NextRequest) => Promise<NextResponse<T>>
) {
  return async (request: NextRequest): Promise<NextResponse> => {
    try {
      return await handler(request);
    } catch (error) {
      return handleError(error, request);
    }
  };
}

function handleError(error: unknown, request: NextRequest): NextResponse {
  const requestId = request.headers.get('x-request-id') || crypto.randomUUID();

  if (error instanceof APIError) {
    // Don't report client errors to Sentry
    if (error.statusCode >= 500) {
      Sentry.captureException(error, {
        extra: {
          requestId,
          path: request.nextUrl.pathname,
          ...error.details,
        },
      });
    }

    return NextResponse.json(
      {
        error: {
          code: error.code,
          message: error.message,
          details: error.details,
          requestId,
        },
      },
      { status: error.statusCode }
    );
  }

  // Unexpected errors
  Sentry.captureException(error, {
    extra: {
      requestId,
      path: request.nextUrl.pathname,
    },
  });

  return NextResponse.json(
    {
      error: {
        code: 'INTERNAL_ERROR',
        message: process.env.NODE_ENV === 'production'
          ? 'An unexpected error occurred'
          : error instanceof Error ? error.message : 'Unknown error',
        requestId,
      },
    },
    { status: 500 }
  );
}

// Usage
// app/api/users/route.ts
import { withErrorHandler, APIError } from '@/lib/api-error-handler';

export const GET = withErrorHandler(async (request) => {
  const users = await db.user.findMany();

  if (!users.length) {
    throw new APIError('No users found', 404, 'NOT_FOUND');
  }

  return NextResponse.json(users);
});
```

---

## 6. Server Action Error Handling

```typescript
// lib/action-error-handler.ts
'use server';

import * as Sentry from '@sentry/nextjs';

type ActionResult<T> =
  | { success: true; data: T }
  | { success: false; error: string; code: string };

export function withSentryAction<T, P extends unknown[]>(
  actionName: string,
  action: (...args: P) => Promise<T>
): (...args: P) => Promise<ActionResult<T>> {
  return async (...args: P): Promise<ActionResult<T>> => {
    return Sentry.withServerActionInstrumentation(
      actionName,
      { recordResponse: true },
      async () => {
        try {
          const result = await action(...args);
          return { success: true, data: result };
        } catch (error) {
          Sentry.captureException(error, {
            extra: { actionName, args: sanitizeArgs(args) },
          });

          return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error',
            code: 'ACTION_ERROR',
          };
        }
      }
    );
  };
}

function sanitizeArgs(args: unknown[]): unknown[] {
  return args.map((arg) => {
    if (typeof arg === 'object' && arg !== null) {
      const sanitized = { ...arg } as Record<string, unknown>;
      delete sanitized.password;
      delete sanitized.token;
      delete sanitized.secret;
      return sanitized;
    }
    return arg;
  });
}

// Usage
// app/actions/user.ts
import { withSentryAction } from '@/lib/action-error-handler';

const createUserImpl = async (data: CreateUserInput) => {
  const user = await db.user.create({ data });
  return user;
};

export const createUser = withSentryAction('createUser', createUserImpl);
```

---

## 7. User Context

```typescript
// lib/sentry-context.ts
import * as Sentry from '@sentry/nextjs';
import { auth } from '@/lib/auth';

export async function setSentryUserContext() {
  const session = await auth();

  if (session?.user) {
    Sentry.setUser({
      id: session.user.id,
      email: session.user.email || undefined,
      username: session.user.name || undefined,
    });

    Sentry.setTag('user_plan', session.user.plan);
    Sentry.setTag('user_role', session.user.role);
  } else {
    Sentry.setUser(null);
  }
}

// Use in layout or middleware
// app/layout.tsx
export default async function RootLayout({ children }) {
  await setSentryUserContext();
  return <html>...</html>;
}
```

---

## 8. Custom Error Classes

```typescript
// lib/errors.ts
export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class ValidationError extends AppError {
  constructor(message: string, public errors: Record<string, string[]>) {
    super(message, 'VALIDATION_ERROR', 400, { errors });
    this.name = 'ValidationError';
  }
}

export class AuthenticationError extends AppError {
  constructor(message = 'Authentication required') {
    super(message, 'UNAUTHENTICATED', 401);
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends AppError {
  constructor(message = 'Permission denied') {
    super(message, 'FORBIDDEN', 403);
    this.name = 'AuthorizationError';
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404);
    this.name = 'NotFoundError';
  }
}

export class RateLimitError extends AppError {
  constructor(retryAfter: number) {
    super('Rate limit exceeded', 'RATE_LIMITED', 429, { retryAfter });
    this.name = 'RateLimitError';
  }
}
```

---

## 9. Transaction Monitoring

```typescript
// lib/sentry-transaction.ts
import * as Sentry from '@sentry/nextjs';

export async function withTransaction<T>(
  name: string,
  operation: string,
  fn: () => Promise<T>,
  data?: Record<string, unknown>
): Promise<T> {
  return Sentry.startSpan(
    {
      name,
      op: operation,
      attributes: data,
    },
    async (span) => {
      try {
        const result = await fn();
        span.setStatus({ code: 1 }); // OK
        return result;
      } catch (error) {
        span.setStatus({ code: 2, message: 'Error' }); // ERROR
        throw error;
      }
    }
  );
}

// Usage
const order = await withTransaction(
  'Create Order',
  'order.create',
  async () => {
    return await orderService.create(data);
  },
  { userId: user.id, amount: data.total }
);
```

---

## 10. Source Maps Upload

```typescript
// scripts/upload-sourcemaps.ts
import { execSync } from 'child_process';

const SENTRY_ORG = process.env.SENTRY_ORG;
const SENTRY_PROJECT = process.env.SENTRY_PROJECT;
const RELEASE = process.env.VERCEL_GIT_COMMIT_SHA || 'development';

// Upload source maps
execSync(
  `npx @sentry/cli releases files ${RELEASE} upload-sourcemaps .next --url-prefix '~/_next'`,
  { stdio: 'inherit' }
);

// Finalize release
execSync(
  `npx @sentry/cli releases finalize ${RELEASE}`,
  { stdio: 'inherit' }
);

console.log(`Source maps uploaded for release: ${RELEASE}`);
```

---

## 11. Testing Error Tracking

```typescript
// app/api/test-error/route.ts
import * as Sentry from '@sentry/nextjs';
import { NextResponse } from 'next/server';

export async function GET() {
  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json({ error: 'Not available in production' }, { status: 403 });
  }

  try {
    throw new Error('Test Sentry error - please ignore');
  } catch (error) {
    Sentry.captureException(error);
    return NextResponse.json({
      message: 'Test error sent to Sentry',
      eventId: Sentry.lastEventId()
    });
  }
}
```
