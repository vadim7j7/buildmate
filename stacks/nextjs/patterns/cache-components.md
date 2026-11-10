# Caching in Next.js 16 (Cache Components)

Read this when a task caches data, invalidates it after a mutation, or touches
`next.config.*` caching options. Check `next.config.*` first: the rules depend on
whether `cacheComponents` is on.

## Two Modes

| `next.config.*` | Data is... | You cache with... |
|---|---|---|
| `cacheComponents: true` | **dynamic by default** (fetched per request) | `'use cache'` + `cacheLife` + `cacheTag` |
| not set (previous model) | per `fetch` options and route segment config | `fetch(url, { next: { revalidate, tags } })`, `export const revalidate` |

Don't mix the models in one project. With Cache Components, the route segment
configs `dynamic`, `revalidate`, `fetchCache` and `runtime` don't apply (remove
them; Cache Components needs the Node.js runtime).

```ts
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true, // set explicitly; unset logs a warning
};

export default nextConfig;
```

The rest of this file is the Cache Components model.

## `'use cache'`

Marks an async function, component, or a whole file (every export) as cached. The
cache key is the build, the function, and its **serializable arguments** (plus any
variables it closes over).

```ts
// src/lib/data/products.ts
import 'server-only';
import { cacheLife, cacheTag } from 'next/cache';

export async function getProducts() {
  'use cache';
  cacheLife('hours');            // always set it explicitly
  cacheTag('products');
  return db.product.findMany({ orderBy: { name: 'asc' } });
}

export async function getProduct(id: string) {
  'use cache';
  cacheLife('days');
  cacheTag('products', `product-${id}`);
  return db.product.findUnique({ where: { id } });
}
```

Rules:

- **No request-time APIs inside**: `cookies()`, `headers()`, `searchParams` throw
  there (also from helpers it calls). Read them outside and pass the values as
  arguments, so the user/tenant is part of the cache key:

  ```ts
  export default async function Page() {
    const user = await requireUser();           // reads cookies: outside the cache
    const projects = await getProjectsFor(user.id);
    // ...
  }

  async function getProjectsFor(userId: string) {
    'use cache';
    cacheLife('minutes');
    cacheTag(`projects-${userId}`);
    return db.project.findMany({ where: { ownerId: userId } });
  }
  ```

- Arguments and return values must be serializable (no class instances,
  functions only as pass-through, e.g. `children` or a Server Action prop).
- `React.cache` values from outside are not visible inside a `'use cache'` scope;
  pass data as arguments.
- Never cache per-user data under a key that doesn't include the user.

## `cacheLife`

Built-in profiles (`stale` / `revalidate` / `expire`):

| Profile | Use for | revalidate | expire |
|---|---|---|---|
| `seconds` | near-real-time | 1 s | 1 min |
| `minutes` | feeds | 1 min | 1 h |
| `hours` | inventory, several updates a day | 1 h | 1 day |
| `days` | articles | 1 day | 1 week |
| `weeks` | rarely updated | 1 week | 30 days |
| `max` | almost static (+ tag invalidation) | 30 days | 1 year |
| `default` (when omitted) | | 15 min | never |

Custom profiles go in `next.config.ts` under `cacheLife: { name: { stale, revalidate, expire } }`;
one-offs as `cacheLife({ revalidate: 900 })`. Very short lifetimes (`seconds`,
`expire` < 5 min) are left out of the prerendered shell and resolve per request:
wrap them in `<Suspense>`.

## Dynamic Content and `<Suspense>`

Anything uncached that reads request data (cookies, headers, `searchParams`,
uncached DB/API calls) must render inside a `<Suspense>` boundary, so Next.js can
prerender the static shell and stream the rest. Otherwise the build fails.

```tsx
export default function Page() {
  return (
    <>
      <ProductList />                      {/* 'use cache': in the static shell */}
      <Suspense fallback={<CartSkeleton />}>
        <Cart />                           {/* reads cookies: streamed per request */}
      </Suspense>
    </>
  );
}
```

## Invalidation After a Mutation

| API | Where | Effect |
|---|---|---|
| `updateTag(tag)` | **Server Actions only** | Expires now; the next read waits for fresh data (read-your-own-writes). Use after the user's own edit. |
| `revalidateTag(tag, 'max')` | Server Actions, Route Handlers (webhooks) | Stale-while-revalidate: serves the old entry once, refreshes in the background. |
| `revalidatePath(path)` | Server Actions, Route Handlers | Invalidates a route; coarser than tags. |

```ts
// src/lib/actions/products.ts
'use server';
import { updateTag } from 'next/cache';

export async function renameProduct(id: string, name: string) {
  const user = await requireAdmin();
  const input = RenameSchema.parse({ id, name });
  await db.product.update({ where: { id: input.id }, data: { name: input.name } });
  updateTag('products');
  updateTag(`product-${input.id}`);
}
```

```ts
// src/app/api/webhooks/cms/route.ts: external change, no user waiting on it
import { revalidateTag } from 'next/cache';

export async function POST(request: Request) {
  await verifySignature(request);
  revalidateTag('products', 'max');
  return Response.json({ ok: true });
}
```

`revalidateTag(tag)` with no profile is the legacy form; always pass one.

## Checklist

- [ ] Every `'use cache'` scope calls `cacheLife` and `cacheTag`
- [ ] No `cookies()` / `headers()` / `searchParams` inside cached scopes
- [ ] User- or tenant-specific data has the user/tenant id in its arguments
- [ ] Each mutation invalidates the tags it affects (`updateTag` in actions)
- [ ] Request-dependent UI sits inside `<Suspense>`
- [ ] Debug with `NEXT_PRIVATE_DEBUG_CACHE=1 npm run dev`
