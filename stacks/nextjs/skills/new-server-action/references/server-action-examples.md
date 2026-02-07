# Server Action Examples

Reference examples for generating Next.js Server Actions.

## Basic CRUD Actions

### Create Action

```typescript
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { db } from '@/lib/db';
import { posts } from '@/lib/db/schema';
import { getCurrentUser } from '@/lib/auth';

const CreatePostSchema = z.object({
  title: z.string().min(1, 'Title is required').max(100, 'Title too long'),
  body: z.string().min(10, 'Body must be at least 10 characters'),
  published: z.boolean().default(false),
});

type CreatePostInput = z.infer<typeof CreatePostSchema>;

type CreatePostResult =
  | { success: true; postId: string }
  | { success: false; error: string; fieldErrors?: Record<string, string[]> };

export async function createPost(input: CreatePostInput): Promise<CreatePostResult> {
  const user = await getCurrentUser();
  if (!user) {
    return { success: false, error: 'Unauthorized' };
  }

  const parsed = CreatePostSchema.safeParse(input);
  if (!parsed.success) {
    return {
      success: false,
      error: 'Validation failed',
      fieldErrors: parsed.error.flatten().fieldErrors as Record<string, string[]>,
    };
  }

  try {
    const [post] = await db
      .insert(posts)
      .values({
        ...parsed.data,
        authorId: user.id,
        publishedAt: parsed.data.published ? new Date() : null,
      })
      .returning({ id: posts.id });

    revalidatePath('/posts');
    revalidatePath(`/users/${user.id}/posts`);

    return { success: true, postId: post.id };
  } catch (error) {
    console.error('Failed to create post:', error);
    return { success: false, error: 'Failed to create post' };
  }
}
```

### Update Action

```typescript
'use server';

import { z } from 'zod';
import { revalidatePath, revalidateTag } from 'next/cache';
import { db } from '@/lib/db';
import { posts } from '@/lib/db/schema';
import { eq, and } from 'drizzle-orm';
import { getCurrentUser } from '@/lib/auth';

const UpdatePostSchema = z.object({
  id: z.string().uuid(),
  title: z.string().min(1, 'Title is required').max(100).optional(),
  body: z.string().min(10).optional(),
  published: z.boolean().optional(),
});

type UpdatePostInput = z.infer<typeof UpdatePostSchema>;

type UpdatePostResult =
  | { success: true }
  | { success: false; error: string; fieldErrors?: Record<string, string[]> };

export async function updatePost(input: UpdatePostInput): Promise<UpdatePostResult> {
  const user = await getCurrentUser();
  if (!user) {
    return { success: false, error: 'Unauthorized' };
  }

  const parsed = UpdatePostSchema.safeParse(input);
  if (!parsed.success) {
    return {
      success: false,
      error: 'Validation failed',
      fieldErrors: parsed.error.flatten().fieldErrors as Record<string, string[]>,
    };
  }

  const { id, ...updates } = parsed.data;

  try {
    // Verify ownership
    const post = await db.query.posts.findFirst({
      where: and(eq(posts.id, id), eq(posts.authorId, user.id)),
    });

    if (!post) {
      return { success: false, error: 'Post not found' };
    }

    // Handle publish state change
    const updateData = {
      ...updates,
      updatedAt: new Date(),
      ...(updates.published === true && !post.publishedAt
        ? { publishedAt: new Date() }
        : {}),
      ...(updates.published === false ? { publishedAt: null } : {}),
    };

    await db.update(posts).set(updateData).where(eq(posts.id, id));

    revalidatePath('/posts');
    revalidatePath(`/posts/${id}`);
    revalidateTag(`post-${id}`);

    return { success: true };
  } catch (error) {
    console.error('Failed to update post:', error);
    return { success: false, error: 'Failed to update post' };
  }
}
```

### Delete Action

```typescript
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { db } from '@/lib/db';
import { posts } from '@/lib/db/schema';
import { eq, and } from 'drizzle-orm';
import { getCurrentUser } from '@/lib/auth';

const DeletePostSchema = z.object({
  id: z.string().uuid(),
});

export async function deletePost(input: z.infer<typeof DeletePostSchema>) {
  const user = await getCurrentUser();
  if (!user) {
    return { success: false, error: 'Unauthorized' };
  }

  const parsed = DeletePostSchema.safeParse(input);
  if (!parsed.success) {
    return { success: false, error: 'Invalid input' };
  }

  try {
    const result = await db
      .delete(posts)
      .where(and(eq(posts.id, parsed.data.id), eq(posts.authorId, user.id)));

    if (result.rowCount === 0) {
      return { success: false, error: 'Post not found' };
    }

    revalidatePath('/posts');
  } catch (error) {
    console.error('Failed to delete post:', error);
    return { success: false, error: 'Failed to delete post' };
  }

  // Redirect after successful deletion
  redirect('/posts');
}
```

## Form Actions

### Contact Form

```typescript
'use server';

import { z } from 'zod';
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

const ContactSchema = z.object({
  name: z.string().min(2, 'Name is too short'),
  email: z.string().email('Invalid email'),
  message: z.string().min(10, 'Message must be at least 10 characters'),
  honeypot: z.string().max(0, 'Bot detected'), // Spam protection
});

type ContactResult =
  | { success: true }
  | { success: false; error: string; fieldErrors?: Record<string, string[]> };

export async function submitContact(
  prevState: ContactResult | null,
  formData: FormData
): Promise<ContactResult> {
  const input = {
    name: formData.get('name'),
    email: formData.get('email'),
    message: formData.get('message'),
    honeypot: formData.get('website') ?? '', // Honeypot field
  };

  const parsed = ContactSchema.safeParse(input);
  if (!parsed.success) {
    return {
      success: false,
      error: 'Validation failed',
      fieldErrors: parsed.error.flatten().fieldErrors as Record<string, string[]>,
    };
  }

  try {
    await resend.emails.send({
      from: 'Contact Form <contact@example.com>',
      to: 'team@example.com',
      subject: `Contact from ${parsed.data.name}`,
      text: `
Name: ${parsed.data.name}
Email: ${parsed.data.email}

Message:
${parsed.data.message}
      `,
    });

    return { success: true };
  } catch (error) {
    console.error('Failed to send contact email:', error);
    return { success: false, error: 'Failed to send message' };
  }
}
```

### File Upload Action

```typescript
'use server';

import { z } from 'zod';
import { put } from '@vercel/blob';
import { getCurrentUser } from '@/lib/auth';

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

const UploadSchema = z.object({
  file: z
    .instanceof(File)
    .refine((file) => file.size <= MAX_FILE_SIZE, 'File too large (max 5MB)')
    .refine(
      (file) => ALLOWED_TYPES.includes(file.type),
      'Invalid file type (JPEG, PNG, WebP only)'
    ),
});

type UploadResult =
  | { success: true; url: string }
  | { success: false; error: string };

export async function uploadImage(formData: FormData): Promise<UploadResult> {
  const user = await getCurrentUser();
  if (!user) {
    return { success: false, error: 'Unauthorized' };
  }

  const file = formData.get('file');
  const parsed = UploadSchema.safeParse({ file });

  if (!parsed.success) {
    return {
      success: false,
      error: parsed.error.errors[0]?.message ?? 'Invalid file',
    };
  }

  try {
    const blob = await put(`uploads/${user.id}/${parsed.data.file.name}`, parsed.data.file, {
      access: 'public',
    });

    return { success: true, url: blob.url };
  } catch (error) {
    console.error('Failed to upload file:', error);
    return { success: false, error: 'Upload failed' };
  }
}
```

## With Authentication

```typescript
'use server';

import { z } from 'zod';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { createSession, verifyPassword } from '@/lib/auth';
import { db } from '@/lib/db';

const LoginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1, 'Password required'),
});

type LoginResult =
  | { success: true }
  | { success: false; error: string };

export async function login(
  prevState: LoginResult | null,
  formData: FormData
): Promise<LoginResult> {
  const parsed = LoginSchema.safeParse({
    email: formData.get('email'),
    password: formData.get('password'),
  });

  if (!parsed.success) {
    return { success: false, error: 'Invalid credentials' };
  }

  const user = await db.query.users.findFirst({
    where: (users, { eq }) => eq(users.email, parsed.data.email),
  });

  if (!user) {
    // Don't reveal whether email exists
    return { success: false, error: 'Invalid credentials' };
  }

  const isValid = await verifyPassword(parsed.data.password, user.passwordHash);
  if (!isValid) {
    return { success: false, error: 'Invalid credentials' };
  }

  // Create session
  const session = await createSession(user.id);

  const cookieStore = await cookies();
  cookieStore.set('session', session.token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 7, // 7 days
  });

  redirect('/dashboard');
}

export async function logout() {
  const cookieStore = await cookies();
  cookieStore.delete('session');
  redirect('/');
}
```

## Test Examples

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPost } from './createPost';

// Mock dependencies
vi.mock('@/lib/db', () => ({
  db: {
    insert: vi.fn().mockReturnValue({
      values: vi.fn().mockReturnValue({
        returning: vi.fn().mockResolvedValue([{ id: 'post-123' }]),
      }),
    }),
  },
}));

vi.mock('@/lib/auth', () => ({
  getCurrentUser: vi.fn(),
}));

vi.mock('next/cache', () => ({
  revalidatePath: vi.fn(),
}));

import { getCurrentUser } from '@/lib/auth';

describe('createPost', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns error when not authenticated', async () => {
    vi.mocked(getCurrentUser).mockResolvedValue(null);

    const result = await createPost({
      title: 'Test',
      body: 'Test content here',
      published: false,
    });

    expect(result).toEqual({ success: false, error: 'Unauthorized' });
  });

  it('returns validation errors for invalid input', async () => {
    vi.mocked(getCurrentUser).mockResolvedValue({ id: 'user-1', email: 'test@test.com' });

    const result = await createPost({
      title: '',
      body: 'short',
      published: false,
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.fieldErrors?.title).toBeDefined();
      expect(result.fieldErrors?.body).toBeDefined();
    }
  });

  it('creates post and returns postId on success', async () => {
    vi.mocked(getCurrentUser).mockResolvedValue({ id: 'user-1', email: 'test@test.com' });

    const result = await createPost({
      title: 'Valid Title',
      body: 'This is a valid body with enough content',
      published: true,
    });

    expect(result).toEqual({ success: true, postId: 'post-123' });
  });
});
```

## Component Integration

```typescript
'use client';

import { useActionState, useFormStatus } from 'react';
import { createPost } from '@/actions/createPost';

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Creating...' : 'Create Post'}
    </button>
  );
}

export function CreatePostForm() {
  const [state, formAction] = useActionState(
    async (prevState: unknown, formData: FormData) => {
      return await createPost({
        title: formData.get('title') as string,
        body: formData.get('body') as string,
        published: formData.get('published') === 'on',
      });
    },
    null
  );

  return (
    <form action={formAction}>
      <div>
        <label htmlFor="title">Title</label>
        <input id="title" name="title" required />
        {state?.fieldErrors?.title && (
          <span className="text-red-500">{state.fieldErrors.title[0]}</span>
        )}
      </div>

      <div>
        <label htmlFor="body">Body</label>
        <textarea id="body" name="body" rows={10} required />
        {state?.fieldErrors?.body && (
          <span className="text-red-500">{state.fieldErrors.body[0]}</span>
        )}
      </div>

      <div>
        <label>
          <input type="checkbox" name="published" />
          Publish immediately
        </label>
      </div>

      <SubmitButton />

      {state?.success === false && !state.fieldErrors && (
        <div className="text-red-500">{state.error}</div>
      )}

      {state?.success && (
        <div className="text-green-500">Post created successfully!</div>
      )}
    </form>
  );
}
```
