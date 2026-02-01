# React Security Checklist

## 1. XSS Prevention

### dangerouslySetInnerHTML

**NEVER** use `dangerouslySetInnerHTML` with unsanitized user input.

```typescript
// DANGEROUS - XSS vulnerability
<div dangerouslySetInnerHTML={{ __html: userProvidedContent }} />

// SAFE - Sanitize first with DOMPurify
import DOMPurify from 'dompurify';

<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userProvidedContent) }} />

// SAFEST - Avoid dangerouslySetInnerHTML entirely
// Use a markdown renderer or plain text rendering
<Text>{userProvidedContent}</Text>
```

### URL-Based XSS

Validate URLs before rendering as links or setting as `src` attributes.

```typescript
// DANGEROUS - Could inject javascript: URLs
<a href={userProvidedUrl}>Click</a>

// SAFE - Validate URL protocol
function isSafeUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:', 'mailto:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}

{isSafeUrl(url) && <a href={url}>Click</a>}
```

### Template Injection

React auto-escapes JSX expressions, but watch out for:

```typescript
// React auto-escapes this - SAFE
<Text>{userInput}</Text>

// But these are NOT safe:
document.innerHTML = userInput;         // UNSAFE
element.insertAdjacentHTML('beforeend', userInput); // UNSAFE
```

---

## 2. Secret Exposure in Client Code

### Environment Variables

Only `NEXT_PUBLIC_` prefixed variables are exposed to the browser.

```bash
# .env
DATABASE_URL=postgres://...          # Server only - SAFE
API_SECRET_KEY=sk_...                # Server only - SAFE
NEXT_PUBLIC_API_URL=https://api...   # Exposed to browser - OK for public URLs
NEXT_PUBLIC_STRIPE_KEY=pk_...        # Exposed to browser - OK for publishable keys

# NEVER put secrets with NEXT_PUBLIC_ prefix
# NEXT_PUBLIC_DATABASE_URL=...       # DANGEROUS - exposed to browser!
# NEXT_PUBLIC_API_SECRET=...         # DANGEROUS - exposed to browser!
```

### Checking for Leaked Secrets

Review code for hardcoded secrets:

```typescript
// DANGEROUS - Secrets in client code
const API_KEY = 'sk_live_abc123';  // NEVER do this in client code

// SAFE - Use server-only environment variables
// In API routes or server components:
const apiKey = process.env.API_SECRET_KEY;

// SAFE - Use public keys in client code only if they're truly public
const stripeKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
```

### Source Maps in Production

Ensure source maps are not deployed to production, as they expose source code:

```typescript
// next.config.js
module.exports = {
  productionBrowserSourceMaps: false, // Default is false - keep it that way
};
```

---

## 3. CORS Configuration

### API Route CORS Headers

```typescript
// src/app/api/projects/route.ts
import { NextRequest, NextResponse } from 'next/server';

const ALLOWED_ORIGINS = [
  'https://myapp.com',
  'https://staging.myapp.com',
];

function getCorsHeaders(origin: string | null) {
  const headers: Record<string, string> = {
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Max-Age': '86400',
  };

  if (origin && ALLOWED_ORIGINS.includes(origin)) {
    headers['Access-Control-Allow-Origin'] = origin;
  }

  return headers;
}

export async function OPTIONS(request: NextRequest) {
  const origin = request.headers.get('origin');
  return new NextResponse(null, {
    status: 204,
    headers: getCorsHeaders(origin),
  });
}
```

### Common CORS Mistakes

```typescript
// DANGEROUS - Allows any origin
'Access-Control-Allow-Origin': '*'

// DANGEROUS - Reflects the origin without validation
'Access-Control-Allow-Origin': request.headers.get('origin')

// SAFE - Whitelist specific origins
const origin = request.headers.get('origin');
if (ALLOWED_ORIGINS.includes(origin)) {
  headers['Access-Control-Allow-Origin'] = origin;
}
```

---

## 4. Input Validation

### Client-Side Validation (UX, Not Security)

Client-side validation improves UX but is NOT a security boundary:

```typescript
// @mantine/form validation - good for UX
const form = useForm({
  validate: {
    email: (value) => (/^\S+@\S+\.\S+$/.test(value) ? null : 'Invalid email'),
    name: (value) => (value.trim().length >= 2 ? null : 'Too short'),
  },
});
```

### Server-Side Validation (Security Boundary)

API routes MUST validate all input:

```typescript
// src/app/api/projects/route.ts
import { z } from 'zod';

const CreateProjectSchema = z.object({
  name: z.string().min(2).max(100).trim(),
  description: z.string().max(1000).trim(),
  status: z.enum(['active', 'archived']).optional().default('active'),
});

export async function POST(request: NextRequest) {
  const body = await request.json();
  const result = CreateProjectSchema.safeParse(body);

  if (!result.success) {
    return NextResponse.json(
      { error: 'Validation failed', details: result.error.flatten() },
      { status: 400 }
    );
  }

  // Use result.data (validated and typed)
  const project = await db.project.create({ data: result.data });
  return NextResponse.json(project, { status: 201 });
}
```

### SQL Injection Prevention

Always use parameterized queries:

```typescript
// DANGEROUS - String interpolation
const result = await db.$queryRaw(`SELECT * FROM projects WHERE id = '${id}'`);

// SAFE - Parameterized query
const result = await db.$queryRaw`SELECT * FROM projects WHERE id = ${id}`;

// SAFE - ORM methods (Prisma, Drizzle)
const result = await db.project.findUnique({ where: { id } });
```

---

## 5. Authentication and Authorization

### Protecting API Routes

```typescript
// src/lib/auth.ts
import { getServerSession } from 'next-auth';
import { NextResponse } from 'next/server';

export async function requireAuth() {
  const session = await getServerSession();
  if (!session?.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  return session;
}

// src/app/api/projects/route.ts
export async function POST(request: NextRequest) {
  const session = await requireAuth();
  if (session instanceof NextResponse) return session; // 401 response

  // Proceed with authenticated request
}
```

### Authorization Checks

```typescript
// Check resource ownership
export async function DELETE(request: NextRequest, { params }: RouteParams) {
  const session = await requireAuth();
  if (session instanceof NextResponse) return session;

  const project = await db.project.findUnique({ where: { id: params.id } });
  if (!project) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 });
  }

  // Authorization check
  if (project.ownerId !== session.user.id) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }

  await db.project.delete({ where: { id: params.id } });
  return new NextResponse(null, { status: 204 });
}
```

---

## 6. Content Security Policy (CSP)

### Next.js Middleware CSP

```typescript
// src/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  response.headers.set(
    'Content-Security-Policy',
    [
      "default-src 'self'",
      "script-src 'self' 'unsafe-eval' 'unsafe-inline'", // Tighten for production
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' blob: data:",
      "font-src 'self'",
      "connect-src 'self' https://api.example.com",
      "frame-ancestors 'none'",
    ].join('; ')
  );

  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

  return response;
}
```

---

## 7. Common Vulnerability Patterns to Watch For

| Vulnerability | How to Detect | Fix |
|---|---|---|
| XSS via `dangerouslySetInnerHTML` | Grep for `dangerouslySetInnerHTML` | Use DOMPurify or avoid entirely |
| Secrets in client code | Grep for `sk_`, `secret`, `password` in `src/` | Move to server-only env vars |
| Missing auth on API routes | Check API routes for auth middleware | Add `requireAuth()` |
| Open redirect | Check `redirect()` and `router.push()` args | Validate URLs against allowlist |
| Prototype pollution | Check for `Object.assign({}, userInput)` | Use structured assignment |
| ReDoS | Check regex patterns used on user input | Use safe regex patterns |
| CSRF | Check state-mutating API routes | Use CSRF tokens or SameSite cookies |
| Clickjacking | Check for `X-Frame-Options` header | Set to `DENY` or `SAMEORIGIN` |

---

## Review Commands

When reviewing for security, run these checks:

```bash
# Find dangerouslySetInnerHTML usage
grep -r "dangerouslySetInnerHTML" src/

# Find potential secrets in client code
grep -rn "secret\|password\|api_key\|token" src/ --include="*.ts" --include="*.tsx" | grep -v "test\|spec\|mock"

# Find eval usage
grep -rn "eval(\|new Function(" src/

# Check for NEXT_PUBLIC_ variables that shouldn't be public
grep -rn "NEXT_PUBLIC_" .env*

# Find unvalidated redirects
grep -rn "redirect(\|router.push(" src/ --include="*.ts" --include="*.tsx"
```
