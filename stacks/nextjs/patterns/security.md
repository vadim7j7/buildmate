# Next.js Security Patterns

Security patterns and best practices for React + Next.js applications. All agents
must follow these patterns to prevent OWASP Top 10 vulnerabilities.

---

## 1. XSS Prevention

React escapes by default, but there are still XSS vectors.

```typescript
// CORRECT - React escapes automatically
function UserProfile({ user }: { user: User }) {
  return <p>{user.bio}</p>;  // Safe, auto-escaped
}

// WRONG - dangerouslySetInnerHTML bypasses escaping
function UserProfile({ user }: { user: User }) {
  return <div dangerouslySetInnerHTML={{ __html: user.bio }} />;  // XSS!
}

// CORRECT - if HTML is needed, sanitize first
import DOMPurify from 'dompurify';

function UserProfile({ user }: { user: User }) {
  const sanitizedBio = DOMPurify.sanitize(user.bio, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'a'],
    ALLOWED_ATTR: ['href'],
  });
  return <div dangerouslySetInnerHTML={{ __html: sanitizedBio }} />;
}
```

### URL Handling

```typescript
// WRONG - javascript: URLs cause XSS
<a href={userProvidedUrl}>Link</a>

// CORRECT - validate URL protocol
function SafeLink({ href, children }: { href: string; children: React.ReactNode }) {
  const isValid = /^https?:\/\//.test(href);
  if (!isValid) {
    return <span>{children}</span>;
  }
  return <a href={href}>{children}</a>;
}

// CORRECT - use URL constructor for validation
function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}
```

---

## 2. Server Actions Security

Server actions run on the server but can be triggered by clients.

```typescript
// WRONG - no authorization check
'use server';

export async function deleteProject(projectId: string) {
  await db.delete(projects).where(eq(projects.id, projectId));
}

// CORRECT - always verify authorization
'use server';

import { auth } from '@/lib/auth';
import { revalidatePath } from 'next/cache';

export async function deleteProject(projectId: string) {
  const session = await auth();
  if (!session?.user) {
    throw new Error('Unauthorized');
  }

  // Verify user owns the project
  const project = await db.query.projects.findFirst({
    where: and(
      eq(projects.id, projectId),
      eq(projects.userId, session.user.id)
    ),
  });

  if (!project) {
    throw new Error('Project not found');
  }

  await db.delete(projects).where(eq(projects.id, projectId));
  revalidatePath('/projects');
}
```

### Input Validation

```typescript
'use server';

import { z } from 'zod';

const createProjectSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(1000).optional(),
  isPublic: z.boolean().default(false),
});

export async function createProject(formData: FormData) {
  const session = await auth();
  if (!session?.user) {
    throw new Error('Unauthorized');
  }

  // Validate input
  const result = createProjectSchema.safeParse({
    name: formData.get('name'),
    description: formData.get('description'),
    isPublic: formData.get('isPublic') === 'true',
  });

  if (!result.success) {
    return { error: result.error.flatten() };
  }

  const project = await db.insert(projects).values({
    ...result.data,
    userId: session.user.id,
  }).returning();

  return { project: project[0] };
}
```

---

## 3. Environment Variables

```typescript
// WRONG - exposes secrets to client
// .env
API_SECRET_KEY=secret123

// app/page.tsx
console.log(process.env.API_SECRET_KEY);  // undefined in client, but...

// WRONG - prefixing makes it available to client
// .env
NEXT_PUBLIC_API_SECRET_KEY=secret123  // Exposed to everyone!

// CORRECT - server-only secrets (no prefix)
// .env
DATABASE_URL=postgres://...
STRIPE_SECRET_KEY=sk_live_...
JWT_SECRET=...

// Client-safe config only
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### Validate Environment at Build

```typescript
// lib/env.ts
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  STRIPE_SECRET_KEY: z.string().startsWith('sk_'),
  JWT_SECRET: z.string().min(32),
  NEXT_PUBLIC_API_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);

// Fails at build time if env vars are missing or invalid
```

---

## 4. Authentication Patterns

### Session Handling

```typescript
// lib/auth.ts
import { cookies } from 'next/headers';
import { SignJWT, jwtVerify } from 'jose';

const secret = new TextEncoder().encode(process.env.JWT_SECRET);

export async function createSession(userId: string) {
  const token = await new SignJWT({ userId })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('24h')
    .sign(secret);

  cookies().set('session', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24, // 24 hours
    path: '/',
  });
}

export async function getSession() {
  const token = cookies().get('session')?.value;
  if (!token) return null;

  try {
    const { payload } = await jwtVerify(token, secret);
    return payload as { userId: string };
  } catch {
    return null;
  }
}

export async function destroySession() {
  cookies().delete('session');
}
```

### Protected Routes

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getSession } from '@/lib/auth';

const protectedPaths = ['/dashboard', '/settings', '/projects'];
const authPaths = ['/login', '/signup'];

export async function middleware(request: NextRequest) {
  const session = await getSession();
  const path = request.nextUrl.pathname;

  // Redirect to login if accessing protected route without session
  if (protectedPaths.some((p) => path.startsWith(p)) && !session) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Redirect to dashboard if accessing auth routes with session
  if (authPaths.some((p) => path.startsWith(p)) && session) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

---

## 5. API Route Security

```typescript
// app/api/projects/route.ts
import { NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { rateLimit } from '@/lib/rate-limit';
import { z } from 'zod';

const createProjectSchema = z.object({
  name: z.string().min(1).max(100),
});

export async function POST(request: Request) {
  // Rate limiting
  const ip = request.headers.get('x-forwarded-for') ?? 'unknown';
  const { success } = await rateLimit.limit(ip);
  if (!success) {
    return NextResponse.json(
      { error: 'Too many requests' },
      { status: 429 }
    );
  }

  // Authentication
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  // Input validation
  const body = await request.json();
  const result = createProjectSchema.safeParse(body);
  if (!result.success) {
    return NextResponse.json(
      { error: 'Invalid input', details: result.error.flatten() },
      { status: 400 }
    );
  }

  // Business logic
  const project = await createProject(result.data, session.user.id);
  return NextResponse.json(project, { status: 201 });
}
```

---

## 6. CSRF Protection

Next.js Server Actions include CSRF protection by default. For API routes:

```typescript
// lib/csrf.ts
import { cookies } from 'next/headers';
import { randomBytes } from 'crypto';

export function generateCsrfToken() {
  const token = randomBytes(32).toString('hex');
  cookies().set('csrf-token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
  });
  return token;
}

export function validateCsrfToken(token: string) {
  const storedToken = cookies().get('csrf-token')?.value;
  return storedToken === token;
}

// API route usage
export async function POST(request: Request) {
  const csrfToken = request.headers.get('x-csrf-token');
  if (!csrfToken || !validateCsrfToken(csrfToken)) {
    return NextResponse.json({ error: 'Invalid CSRF token' }, { status: 403 });
  }
  // ... rest of handler
}
```

---

## 7. Content Security Policy

```typescript
// next.config.js
const cspHeader = `
  default-src 'self';
  script-src 'self' 'unsafe-eval' 'unsafe-inline';
  style-src 'self' 'unsafe-inline';
  img-src 'self' blob: data: https:;
  font-src 'self';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
  frame-ancestors 'none';
  upgrade-insecure-requests;
`;

module.exports = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: cspHeader.replace(/\n/g, ''),
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ];
  },
};
```

---

## 8. SQL Injection Prevention

When using raw SQL or ORMs, always use parameterized queries.

```typescript
// WRONG - SQL injection
const users = await db.execute(
  `SELECT * FROM users WHERE email = '${email}'`
);

// CORRECT - parameterized query (Drizzle)
const users = await db.select().from(users).where(eq(users.email, email));

// CORRECT - parameterized raw query
const users = await db.execute(
  sql`SELECT * FROM users WHERE email = ${email}`
);

// CORRECT - Prisma (parameterized by default)
const users = await prisma.user.findMany({
  where: { email },
});
```

---

## 9. File Upload Security

```typescript
// app/api/upload/route.ts
import { NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { writeFile } from 'fs/promises';
import { join } from 'path';
import crypto from 'crypto';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_SIZE = 5 * 1024 * 1024; // 5MB

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const formData = await request.formData();
  const file = formData.get('file') as File;

  if (!file) {
    return NextResponse.json({ error: 'No file provided' }, { status: 400 });
  }

  // Validate file type
  if (!ALLOWED_TYPES.includes(file.type)) {
    return NextResponse.json(
      { error: 'Invalid file type. Allowed: JPEG, PNG, WebP' },
      { status: 400 }
    );
  }

  // Validate file size
  if (file.size > MAX_SIZE) {
    return NextResponse.json(
      { error: 'File too large. Maximum: 5MB' },
      { status: 400 }
    );
  }

  // Generate safe filename
  const ext = file.name.split('.').pop();
  const filename = `${crypto.randomUUID()}.${ext}`;
  const buffer = Buffer.from(await file.arrayBuffer());

  // Store file (use cloud storage in production)
  const uploadDir = join(process.cwd(), 'uploads');
  await writeFile(join(uploadDir, filename), buffer);

  return NextResponse.json({ filename });
}
```

---

## 10. Sensitive Data Handling

```typescript
// WRONG - logging sensitive data
console.log('User login:', { email, password });

// CORRECT - redact sensitive fields
console.log('User login:', { email, password: '[REDACTED]' });

// WRONG - returning password hash
export async function GET() {
  const users = await db.select().from(users);
  return NextResponse.json(users);  // Includes passwordHash!
}

// CORRECT - exclude sensitive fields
export async function GET() {
  const users = await db.select({
    id: users.id,
    email: users.email,
    name: users.name,
  }).from(users);
  return NextResponse.json(users);
}

// CORRECT - use a presenter/serializer
function serializeUser(user: User) {
  return {
    id: user.id,
    email: user.email,
    name: user.name,
    createdAt: user.createdAt,
  };
}
```

---

## Security Checklist

Before deploying any feature, verify:

- [ ] No `dangerouslySetInnerHTML` with unsanitized input
- [ ] Server actions check authentication and authorization
- [ ] All user input validated with Zod or similar
- [ ] Secrets not exposed via `NEXT_PUBLIC_` prefix
- [ ] API routes implement rate limiting
- [ ] CSRF protection for state-changing operations
- [ ] Security headers configured in next.config.js
- [ ] File uploads validated (type, size)
- [ ] Sensitive data not logged or returned in responses
- [ ] SQL queries use parameterization
