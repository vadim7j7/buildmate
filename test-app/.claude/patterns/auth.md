# Next.js Authentication Patterns

Authentication patterns using NextAuth.js (Auth.js) v5.

---

## 1. NextAuth.js Setup

### Installation

```bash
npm install next-auth@beta
```

### Configuration

```typescript
// auth.ts
import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import Google from 'next-auth/providers/google';
import GitHub from 'next-auth/providers/github';
import { DrizzleAdapter } from '@auth/drizzle-adapter';
import { db } from '@/lib/db';
import { verifyPassword } from '@/lib/auth/password';

export const { handlers, signIn, signOut, auth } = NextAuth({
  adapter: DrizzleAdapter(db),
  session: { strategy: 'jwt' },
  pages: {
    signIn: '/login',
    error: '/login',
  },
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    GitHub({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    }),
    Credentials({
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const user = await db.query.users.findFirst({
          where: (users, { eq }) => eq(users.email, credentials.email as string),
        });

        if (!user || !user.passwordHash) {
          return null;
        }

        const isValid = await verifyPassword(
          credentials.password as string,
          user.passwordHash
        );

        if (!isValid) {
          return null;
        }

        return {
          id: user.id,
          email: user.email,
          name: user.name,
          image: user.image,
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (token?.id) {
        session.user.id = token.id as string;
      }
      return session;
    },
  },
});
```

### Route Handlers

```typescript
// app/api/auth/[...nextauth]/route.ts
import { handlers } from '@/auth';

export const { GET, POST } = handlers;
```

---

## 2. Middleware Protection

```typescript
// middleware.ts
import { auth } from '@/auth';

export default auth((req) => {
  const { nextUrl } = req;
  const isLoggedIn = !!req.auth;

  const isAuthPage = nextUrl.pathname.startsWith('/login') ||
                     nextUrl.pathname.startsWith('/register');
  const isProtectedPage = nextUrl.pathname.startsWith('/dashboard') ||
                          nextUrl.pathname.startsWith('/settings');
  const isAdminPage = nextUrl.pathname.startsWith('/admin');

  // Redirect logged-in users away from auth pages
  if (isAuthPage && isLoggedIn) {
    return Response.redirect(new URL('/dashboard', nextUrl));
  }

  // Redirect non-logged-in users to login
  if (isProtectedPage && !isLoggedIn) {
    const callbackUrl = encodeURIComponent(nextUrl.pathname);
    return Response.redirect(new URL(`/login?callbackUrl=${callbackUrl}`, nextUrl));
  }

  // Check admin access
  if (isAdminPage) {
    if (!isLoggedIn) {
      return Response.redirect(new URL('/login', nextUrl));
    }
    // Additional admin check would go here
  }

  return;
});

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

---

## 3. Server-Side Authentication

### Getting Session in Server Components

```typescript
// app/dashboard/page.tsx
import { auth } from '@/auth';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const session = await auth();

  if (!session?.user) {
    redirect('/login');
  }

  return (
    <div>
      <h1>Welcome, {session.user.name}</h1>
    </div>
  );
}
```

### Getting Session in Server Actions

```typescript
// actions/profile.ts
'use server';

import { auth } from '@/auth';
import { db } from '@/lib/db';

export async function updateProfile(formData: FormData) {
  const session = await auth();

  if (!session?.user) {
    return { error: 'Unauthorized' };
  }

  const name = formData.get('name') as string;

  await db.update(users)
    .set({ name })
    .where(eq(users.id, session.user.id));

  return { success: true };
}
```

---

## 4. Client-Side Authentication

### Session Provider

```typescript
// app/providers.tsx
'use client';

import { SessionProvider } from 'next-auth/react';
import type { ReactNode } from 'react';

export function Providers({ children }: { children: ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>;
}

// app/layout.tsx
import { Providers } from './providers';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

### Using Session in Client Components

```typescript
// components/UserMenu.tsx
'use client';

import { useSession, signOut } from 'next-auth/react';

export function UserMenu() {
  const { data: session, status } = useSession();

  if (status === 'loading') {
    return <div>Loading...</div>;
  }

  if (!session) {
    return <LoginButton />;
  }

  return (
    <div>
      <span>{session.user.name}</span>
      <button onClick={() => signOut({ callbackUrl: '/' })}>
        Sign Out
      </button>
    </div>
  );
}
```

---

## 5. Sign In/Out Actions

### Server Actions

```typescript
// actions/auth.ts
'use server';

import { signIn, signOut } from '@/auth';
import { AuthError } from 'next-auth';

export async function loginWithCredentials(
  prevState: { error?: string } | undefined,
  formData: FormData
) {
  try {
    await signIn('credentials', {
      email: formData.get('email'),
      password: formData.get('password'),
      redirectTo: '/dashboard',
    });
  } catch (error) {
    if (error instanceof AuthError) {
      switch (error.type) {
        case 'CredentialsSignin':
          return { error: 'Invalid credentials' };
        default:
          return { error: 'Something went wrong' };
      }
    }
    throw error;
  }
}

export async function loginWithGoogle() {
  await signIn('google', { redirectTo: '/dashboard' });
}

export async function loginWithGitHub() {
  await signIn('github', { redirectTo: '/dashboard' });
}

export async function logout() {
  await signOut({ redirectTo: '/' });
}
```

### Login Form

```typescript
// components/LoginForm.tsx
'use client';

import { useActionState } from 'react';
import { loginWithCredentials, loginWithGoogle, loginWithGitHub } from '@/actions/auth';

export function LoginForm() {
  const [state, formAction, isPending] = useActionState(loginWithCredentials, undefined);

  return (
    <div className="space-y-4">
      <form action={formAction} className="space-y-4">
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            required
          />
        </div>
        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            required
          />
        </div>

        {state?.error && (
          <div className="text-red-500">{state.error}</div>
        )}

        <button type="submit" disabled={isPending}>
          {isPending ? 'Signing in...' : 'Sign In'}
        </button>
      </form>

      <div className="flex gap-4">
        <form action={loginWithGoogle}>
          <button type="submit">Sign in with Google</button>
        </form>
        <form action={loginWithGitHub}>
          <button type="submit">Sign in with GitHub</button>
        </form>
      </div>
    </div>
  );
}
```

---

## 6. Registration

```typescript
// actions/register.ts
'use server';

import { z } from 'zod';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { hashPassword } from '@/lib/auth/password';
import { signIn } from '@/auth';

const RegisterSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(8),
});

export async function register(prevState: unknown, formData: FormData) {
  const parsed = RegisterSchema.safeParse({
    name: formData.get('name'),
    email: formData.get('email'),
    password: formData.get('password'),
  });

  if (!parsed.success) {
    return {
      error: 'Validation failed',
      fieldErrors: parsed.error.flatten().fieldErrors,
    };
  }

  const { name, email, password } = parsed.data;

  // Check if user exists
  const existingUser = await db.query.users.findFirst({
    where: (users, { eq }) => eq(users.email, email),
  });

  if (existingUser) {
    return { error: 'Email already registered' };
  }

  // Create user
  const passwordHash = await hashPassword(password);
  await db.insert(users).values({
    name,
    email,
    passwordHash,
  });

  // Sign in immediately
  await signIn('credentials', {
    email,
    password,
    redirectTo: '/dashboard',
  });
}
```

---

## 7. Password Utilities

```typescript
// lib/auth/password.ts
import { hash, verify } from '@node-rs/argon2';

export async function hashPassword(password: string): Promise<string> {
  return hash(password, {
    memoryCost: 19456,
    timeCost: 2,
    outputLen: 32,
    parallelism: 1,
  });
}

export async function verifyPassword(
  password: string,
  hashedPassword: string
): Promise<boolean> {
  try {
    return await verify(hashedPassword, password);
  } catch {
    return false;
  }
}
```

---

## 8. Type Augmentation

```typescript
// types/next-auth.d.ts
import { DefaultSession } from 'next-auth';

declare module 'next-auth' {
  interface Session {
    user: {
      id: string;
    } & DefaultSession['user'];
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    id: string;
  }
}
```

---

## 9. Protected API Routes

```typescript
// app/api/profile/route.ts
import { auth } from '@/auth';
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET() {
  const session = await auth();

  if (!session?.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const user = await db.query.users.findFirst({
    where: (users, { eq }) => eq(users.id, session.user.id),
  });

  return NextResponse.json({ user });
}
```

---

## 10. Testing Authentication

```typescript
// __tests__/auth.test.ts
import { describe, it, expect, vi } from 'vitest';

// Mock next-auth
vi.mock('@/auth', () => ({
  auth: vi.fn(),
  signIn: vi.fn(),
  signOut: vi.fn(),
}));

import { auth } from '@/auth';

describe('Authentication', () => {
  it('returns null when not authenticated', async () => {
    vi.mocked(auth).mockResolvedValue(null);

    const session = await auth();
    expect(session).toBeNull();
  });

  it('returns session when authenticated', async () => {
    vi.mocked(auth).mockResolvedValue({
      user: { id: '1', name: 'Test', email: 'test@test.com' },
      expires: new Date().toISOString(),
    });

    const session = await auth();
    expect(session?.user.id).toBe('1');
  });
});
```
