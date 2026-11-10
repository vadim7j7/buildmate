# Pagination in Express + Prisma

Read this when adding or changing a list endpoint. Every list endpoint is paginated
with a server-side maximum page size; an unbounded `findMany()` is a bug.

If the project's list endpoints already return bare arrays with pagination in
headers, keep that contract. For new APIs use the envelopes below.

## Choose

| Style | Use when | Trade-off |
|---|---|---|
| **Cursor** (`?cursor=<id>&limit=20`) | feeds, infinite scroll, large or fast-changing tables | No "page 7 of 20"; stable under inserts; fast at any depth |
| **Offset** (`?page=2&limit=20`) | admin tables that need page numbers and totals | Slow at deep offsets; rows shift when data changes |

## Cursor Pagination

```typescript
// src/schemas/pagination.ts
import { z } from 'zod';

export const cursorQuerySchema = z.object({
  cursor: z.uuid().optional(),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});
export type CursorQuery = z.infer<typeof cursorQuerySchema>;

export type CursorPage<T> = { items: T[]; nextCursor: string | null };
```

```typescript
// src/services/project-service.ts
async listPage(ownerId: string, { cursor, limit }: CursorQuery): Promise<CursorPage<Project>> {
  const rows = await prisma.project.findMany({
    where: { ownerId },
    orderBy: [{ createdAt: 'desc' }, { id: 'desc' }], // unique tiebreaker: stable order
    take: limit + 1,                                   // one extra row tells us if there is more
    ...(cursor ? { cursor: { id: cursor }, skip: 1 } : {}),
  });

  const hasMore = rows.length > limit;
  const items = hasMore ? rows.slice(0, limit) : rows;
  return { items, nextCursor: hasMore ? items[items.length - 1].id : null };
}
```

```typescript
// src/controllers/project-controller.ts
list = async (req: Request, res: Response) => {
  const query = cursorQuerySchema.parse(req.query); // req.query is read-only in Express 5
  res.json(await this.service.listPage(req.user.id, query));
};
```

The order must be deterministic and match an index (`@@index([ownerId, createdAt, id])`
in `schema.prisma`). A cursor id that belongs to another user simply yields no rows,
because `where` still scopes by owner.

## Offset Pagination

```typescript
export const pageQuerySchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

async listPaged(ownerId: string, { page, limit }: z.infer<typeof pageQuerySchema>) {
  const where = { ownerId };
  const [items, total] = await prisma.$transaction([
    prisma.project.findMany({ where, orderBy: { createdAt: 'desc' }, skip: (page - 1) * limit, take: limit }),
    prisma.project.count({ where }),
  ]);
  return { items, page, limit, total, totalPages: Math.ceil(total / limit) };
}
```

Cap `page` too for very large tables (or switch to cursor): `skip` of 100 000 rows
still reads them.

## Filters and Sorting

- Parse filters with Zod into a typed object and build the Prisma `where` from it;
  never pass `req.query` keys into `where` or `orderBy` directly.
- Sorting: an enum of allowed fields (`z.enum(['createdAt', 'name'])`) plus direction,
  always with `id` as the final tiebreaker.

## Tests

Cover: default limit, `limit` above the maximum (422), last page has `nextCursor: null`,
no duplicates or gaps when walking all pages, another user's rows never appear.
