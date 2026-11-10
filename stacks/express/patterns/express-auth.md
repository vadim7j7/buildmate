# Authentication in Express

Read this when a task adds sign-in, tokens, roles, or protects routes. If the
project already has an auth setup, follow it; this is the default for a new API.

Default: short-lived **JWT access tokens** sent as `Authorization: Bearer <token>`,
verified with `jose`. Tokens are issued either by this API (email + password) or by
an external identity provider (Auth0, Clerk, Cognito...), verified against its JWKS.
A Next.js / Nuxt frontend in front of the API keeps the token server-side (session
cookie) and forwards it.

## Verify Tokens

```typescript
// src/lib/auth.ts
import { jwtVerify, SignJWT, createRemoteJWKSet, type JWTPayload } from 'jose';
import { env } from '@/lib/env';
import { UnauthorizedError } from '@/lib/errors';

export type AuthUser = { id: string; role: 'admin' | 'member' };

const secret = new TextEncoder().encode(env.JWT_SECRET);           // own tokens (HS256)
// const jwks = createRemoteJWKSet(new URL(env.AUTH_JWKS_URL));    // external IdP (RS256)

export async function verifyToken(token: string): Promise<AuthUser> {
  try {
    const { payload } = await jwtVerify(token, secret, {
      issuer: env.JWT_ISSUER,
      audience: env.JWT_AUDIENCE,
      algorithms: ['HS256'],                                        // pin the algorithm
    });
    return toAuthUser(payload);
  } catch {
    throw new UnauthorizedError('Invalid or expired token');
  }
}

export async function signAccessToken(user: AuthUser): Promise<string> {
  return new SignJWT({ role: user.role })
    .setProtectedHeader({ alg: 'HS256' })
    .setSubject(user.id)
    .setIssuer(env.JWT_ISSUER)
    .setAudience(env.JWT_AUDIENCE)
    .setIssuedAt()
    .setExpirationTime('15m')
    .sign(secret);
}

function toAuthUser(payload: JWTPayload): AuthUser {
  if (!payload.sub || (payload.role !== 'admin' && payload.role !== 'member')) {
    throw new UnauthorizedError('Invalid token claims');
  }
  return { id: payload.sub, role: payload.role };
}
```

`UnauthorizedError` is an `AppError` with `statusCode = 401`, so the error handler
answers 401.

## Middleware

```typescript
// src/middleware/auth.ts
import type { Request, Response, NextFunction } from 'express';
import { verifyToken, type AuthUser } from '@/lib/auth';
import { ForbiddenError, UnauthorizedError } from '@/lib/errors';

declare global {
  namespace Express {
    interface Request {
      user: AuthUser;
    }
  }
}

export async function authenticate(req: Request, _res: Response, next: NextFunction) {
  const header = req.get('authorization');
  if (!header?.startsWith('Bearer ')) throw new UnauthorizedError('Missing token');
  req.user = await verifyToken(header.slice('Bearer '.length));
  next();
}

export function requireRole(...roles: AuthUser['role'][]) {
  return (req: Request, _res: Response, next: NextFunction) => {
    if (!roles.includes(req.user.role)) throw new ForbiddenError();
    next();
  };
}

// router.use(authenticate);
// router.delete('/:id', requireRole('admin'), controller.delete);
```

Roles gate *kinds* of actions; ownership of a *record* is checked in the service
query (`where: { id, ownerId: req.user.id }`). Both are needed.

## Email + Password Login

```typescript
// src/services/auth-service.ts
import { hash, verify } from '@node-rs/argon2';

export class AuthService {
  async register(email: string, password: string) {
    const passwordHash = await hash(password);            // argon2id
    return prisma.user.create({ data: { email: email.toLowerCase(), passwordHash } });
  }

  async login(email: string, password: string): Promise<string> {
    const user = await prisma.user.findUnique({ where: { email: email.toLowerCase() } });
    // Same error (and similar timing) for unknown email and wrong password
    const ok = user ? await verify(user.passwordHash, password) : await hash(password).then(() => false);
    if (!user || !ok) throw new UnauthorizedError('Invalid credentials');
    return signAccessToken({ id: user.id, role: user.role });
  }
}
```

- Hash with argon2id (or bcrypt cost ≥ 12); never store or log plain passwords.
- Rate-limit login, sign-up and reset (`express-security.md`).
- Password reset tokens: random (`crypto.randomBytes(32)`), stored hashed, single use,
  expire in ≤ 1 hour; the reset response doesn't reveal whether the email exists.

## Refresh Tokens (when the API issues its own tokens)

- Access token 5–15 min; refresh token long-lived, random, stored **hashed** in the DB
  with user id, expiry and a family id.
- Rotate on every use; if a used refresh token comes back, revoke the whole family
  (token theft).
- Browser clients get the refresh token in an `httpOnly`, `secure`, `sameSite=strict`
  cookie scoped to the refresh path; never in `localStorage`.
- Logout deletes the refresh token server-side.

## Testing

Sign tokens in tests with the same helper (`signAccessToken`) and a test secret;
cover 401 without/with an expired token, 403 for the wrong role, and 404 for another
user's record (`express-testing.md`).
