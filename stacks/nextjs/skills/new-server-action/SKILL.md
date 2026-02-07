---
name: new-server-action
description: Generate a Next.js Server Action with Zod validation
---

# /new-server-action

## What This Does

Creates a Next.js Server Action with Zod schema validation, proper error
handling, and TypeScript types. Server Actions enable secure server-side
mutations from React components.

## Usage

```
/new-server-action createUser         # Creates createUser action
/new-server-action updateProfile      # Creates updateProfile action
/new-server-action submitContact      # Creates submitContact action
/new-server-action deletePost         # Creates deletePost action
```

## How It Works

### 1. Determine Action Purpose

Based on the action name, infer:
- What data the action accepts
- What validation is needed
- What side effects occur (database, email, etc.)
- What response format to return

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` for conventions
- `skills/new-server-action/references/server-action-examples.md` for examples
- Existing actions in `src/app/actions/` or `src/actions/`

### 3. Generate Files

#### Action: `src/actions/<actionName>.ts`

```typescript
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';

const <ActionName>Schema = z.object({
  // Input validation schema
});

type <ActionName>Input = z.infer<typeof <ActionName>Schema>;

type <ActionName>Result =
  | { success: true; data: <ReturnType> }
  | { success: false; error: string; fieldErrors?: Record<string, string[]> };

export async function <actionName>(input: <ActionName>Input): Promise<<ActionName>Result> {
  // Validate input
  const parsed = <ActionName>Schema.safeParse(input);
  if (!parsed.success) {
    return {
      success: false,
      error: 'Validation failed',
      fieldErrors: parsed.error.flatten().fieldErrors,
    };
  }

  try {
    // Perform action
    const result = await doSomething(parsed.data);

    // Revalidate cache if needed
    revalidatePath('/path');

    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: 'Operation failed' };
  }
}
```

#### Test: `src/actions/<actionName>.test.ts`

Tests for validation, success, and error cases.

### 4. Verify

Run type checking:
```bash
npx tsc --noEmit
```

## Rules

- Always use `'use server'` directive at the top
- Validate all inputs with Zod
- Return discriminated unions for type-safe error handling
- Never trust client input - always validate server-side
- Use `revalidatePath` or `revalidateTag` after mutations
- Handle errors gracefully - never expose internal details
- Use `redirect()` for navigation after mutations (throws, not returns)

## Generated Files

```
src/actions/<actionName>.ts
src/actions/<actionName>.test.ts
```

## Example Output

For `/new-server-action createUser`:

**Action:** `src/actions/createUser.ts`
```typescript
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

const CreateUserSchema = z.object({
  email: z.string().email('Invalid email address'),
  name: z.string().min(2, 'Name must be at least 2 characters'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain an uppercase letter')
    .regex(/[0-9]/, 'Password must contain a number'),
});

type CreateUserInput = z.infer<typeof CreateUserSchema>;

type CreateUserResult =
  | { success: true; userId: string }
  | { success: false; error: string; fieldErrors?: Record<string, string[]> };

export async function createUser(input: CreateUserInput): Promise<CreateUserResult> {
  // Validate input
  const parsed = CreateUserSchema.safeParse(input);
  if (!parsed.success) {
    return {
      success: false,
      error: 'Validation failed',
      fieldErrors: parsed.error.flatten().fieldErrors as Record<string, string[]>,
    };
  }

  const { email, name, password } = parsed.data;

  try {
    // Check for existing user
    const existingUser = await db.query.users.findFirst({
      where: (users, { eq }) => eq(users.email, email),
    });

    if (existingUser) {
      return {
        success: false,
        error: 'Email already registered',
        fieldErrors: { email: ['Email already registered'] },
      };
    }

    // Hash password
    const hashedPassword = await hashPassword(password);

    // Create user
    const [user] = await db
      .insert(users)
      .values({
        email,
        name,
        passwordHash: hashedPassword,
      })
      .returning({ id: users.id });

    // Revalidate users list
    revalidatePath('/admin/users');

    return { success: true, userId: user.id };
  } catch (error) {
    console.error('Failed to create user:', error);
    return { success: false, error: 'Failed to create user' };
  }
}
```

**Component Usage:**
```typescript
'use client';

import { useActionState } from 'react';
import { createUser } from '@/actions/createUser';

export function SignUpForm() {
  const [state, formAction, isPending] = useActionState(
    async (prevState: unknown, formData: FormData) => {
      const result = await createUser({
        email: formData.get('email') as string,
        name: formData.get('name') as string,
        password: formData.get('password') as string,
      });
      return result;
    },
    null
  );

  return (
    <form action={formAction}>
      <input name="email" type="email" required />
      {state?.fieldErrors?.email && (
        <span className="error">{state.fieldErrors.email[0]}</span>
      )}

      <input name="name" type="text" required />
      {state?.fieldErrors?.name && (
        <span className="error">{state.fieldErrors.name[0]}</span>
      )}

      <input name="password" type="password" required />
      {state?.fieldErrors?.password && (
        <span className="error">{state.fieldErrors.password[0]}</span>
      )}

      <button type="submit" disabled={isPending}>
        {isPending ? 'Creating...' : 'Create Account'}
      </button>

      {state?.error && !state.fieldErrors && (
        <div className="error">{state.error}</div>
      )}
    </form>
  );
}
```
