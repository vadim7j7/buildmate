# Next.js Pagination Patterns

Pagination patterns for Next.js App Router with Server Components.

---

## 1. URL-Based Pagination (Server Components)

### Page Component

```typescript
// app/posts/page.tsx
import { Suspense } from 'react';
import { PostList } from '@/components/posts/PostList';
import { Pagination } from '@/components/ui/Pagination';
import { getPosts } from '@/lib/data/posts';

type SearchParams = Promise<{
  page?: string;
  per_page?: string;
}>;

export default async function PostsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  const page = Number(params.page) || 1;
  const perPage = Number(params.per_page) || 20;

  const { posts, totalCount, totalPages } = await getPosts({
    page,
    perPage,
  });

  return (
    <div className="space-y-6">
      <h1>Posts</h1>

      <Suspense fallback={<PostListSkeleton />}>
        <PostList posts={posts} />
      </Suspense>

      <Pagination
        currentPage={page}
        totalPages={totalPages}
        baseUrl="/posts"
      />
    </div>
  );
}
```

### Pagination Component

```typescript
// components/ui/Pagination.tsx
import Link from 'next/link';
import { ChevronLeft, ChevronRight } from 'lucide-react';

type PaginationProps = {
  currentPage: number;
  totalPages: number;
  baseUrl: string;
};

export function Pagination({ currentPage, totalPages, baseUrl }: PaginationProps) {
  const pages = generatePageNumbers(currentPage, totalPages);

  return (
    <nav className="flex items-center justify-center gap-2" aria-label="Pagination">
      <PaginationLink
        href={currentPage > 1 ? `${baseUrl}?page=${currentPage - 1}` : undefined}
        disabled={currentPage <= 1}
        aria-label="Previous page"
      >
        <ChevronLeft className="h-4 w-4" />
      </PaginationLink>

      {pages.map((page, index) => (
        page === '...' ? (
          <span key={`ellipsis-${index}`} className="px-2">...</span>
        ) : (
          <PaginationLink
            key={page}
            href={`${baseUrl}?page=${page}`}
            isActive={page === currentPage}
          >
            {page}
          </PaginationLink>
        )
      ))}

      <PaginationLink
        href={currentPage < totalPages ? `${baseUrl}?page=${currentPage + 1}` : undefined}
        disabled={currentPage >= totalPages}
        aria-label="Next page"
      >
        <ChevronRight className="h-4 w-4" />
      </PaginationLink>
    </nav>
  );
}

function PaginationLink({
  href,
  disabled,
  isActive,
  children,
  ...props
}: {
  href?: string;
  disabled?: boolean;
  isActive?: boolean;
  children: React.ReactNode;
} & React.HTMLAttributes<HTMLAnchorElement>) {
  const className = `
    px-3 py-2 rounded-md text-sm font-medium
    ${isActive ? 'bg-primary text-white' : 'hover:bg-gray-100'}
    ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
  `;

  if (disabled || !href) {
    return <span className={className} {...props}>{children}</span>;
  }

  return (
    <Link href={href} className={className} {...props}>
      {children}
    </Link>
  );
}

function generatePageNumbers(current: number, total: number): (number | '...')[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  if (current <= 3) {
    return [1, 2, 3, 4, 5, '...', total];
  }

  if (current >= total - 2) {
    return [1, '...', total - 4, total - 3, total - 2, total - 1, total];
  }

  return [1, '...', current - 1, current, current + 1, '...', total];
}
```

---

## 2. Data Fetching with Pagination

```typescript
// lib/data/posts.ts
import { db } from '@/lib/db';
import { posts } from '@/lib/db/schema';
import { desc, count } from 'drizzle-orm';

type GetPostsOptions = {
  page?: number;
  perPage?: number;
};

export async function getPosts({ page = 1, perPage = 20 }: GetPostsOptions = {}) {
  const offset = (page - 1) * perPage;

  const [data, [{ total }]] = await Promise.all([
    db.query.posts.findMany({
      orderBy: [desc(posts.createdAt)],
      limit: perPage,
      offset,
      with: {
        author: true,
      },
    }),
    db.select({ total: count() }).from(posts),
  ]);

  return {
    posts: data,
    totalCount: total,
    totalPages: Math.ceil(total / perPage),
    currentPage: page,
    perPage,
  };
}
```

---

## 3. Cursor-Based Pagination with Infinite Scroll

### Hook

```typescript
// hooks/useInfiniteScroll.ts
'use client';

import { useCallback, useEffect, useRef, useState, useTransition } from 'react';

type UseInfiniteScrollOptions<T> = {
  initialData: T[];
  initialCursor: string | null;
  fetchMore: (cursor: string) => Promise<{ items: T[]; nextCursor: string | null }>;
};

export function useInfiniteScroll<T>({
  initialData,
  initialCursor,
  fetchMore,
}: UseInfiniteScrollOptions<T>) {
  const [items, setItems] = useState<T[]>(initialData);
  const [cursor, setCursor] = useState<string | null>(initialCursor);
  const [isPending, startTransition] = useTransition();
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  const loadMore = useCallback(async () => {
    if (!cursor || isPending) return;

    startTransition(async () => {
      const { items: newItems, nextCursor } = await fetchMore(cursor);
      setItems((prev) => [...prev, ...newItems]);
      setCursor(nextCursor);
    });
  }, [cursor, fetchMore, isPending]);

  useEffect(() => {
    const element = loadMoreRef.current;
    if (!element) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          loadMore();
        }
      },
      { threshold: 0.1 }
    );

    observerRef.current.observe(element);

    return () => {
      observerRef.current?.disconnect();
    };
  }, [loadMore]);

  return {
    items,
    hasMore: !!cursor,
    isLoading: isPending,
    loadMoreRef,
  };
}
```

### Server Action

```typescript
// actions/posts.ts
'use server';

import { db } from '@/lib/db';
import { posts } from '@/lib/db/schema';
import { desc, lt, and } from 'drizzle-orm';

export async function fetchMorePosts(cursor: string) {
  const decoded = JSON.parse(Buffer.from(cursor, 'base64').toString());
  const limit = 20;

  const data = await db.query.posts.findMany({
    where: and(
      lt(posts.createdAt, new Date(decoded.createdAt)),
      lt(posts.id, decoded.id)
    ),
    orderBy: [desc(posts.createdAt), desc(posts.id)],
    limit: limit + 1,
    with: { author: true },
  });

  const hasMore = data.length > limit;
  const items = hasMore ? data.slice(0, limit) : data;

  const nextCursor = hasMore
    ? Buffer.from(
        JSON.stringify({
          createdAt: items[items.length - 1]!.createdAt.toISOString(),
          id: items[items.length - 1]!.id,
        })
      ).toString('base64')
    : null;

  return { items, nextCursor };
}
```

### Component

```typescript
// components/posts/InfinitePostList.tsx
'use client';

import { useInfiniteScroll } from '@/hooks/useInfiniteScroll';
import { fetchMorePosts } from '@/actions/posts';
import { PostCard } from './PostCard';
import type { Post } from '@/lib/db/schema';

type InfinitePostListProps = {
  initialPosts: Post[];
  initialCursor: string | null;
};

export function InfinitePostList({
  initialPosts,
  initialCursor,
}: InfinitePostListProps) {
  const { items, hasMore, isLoading, loadMoreRef } = useInfiniteScroll({
    initialData: initialPosts,
    initialCursor,
    fetchMore: fetchMorePosts,
  });

  return (
    <div className="space-y-4">
      {items.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}

      <div ref={loadMoreRef} className="h-10">
        {isLoading && <LoadingSpinner />}
        {!hasMore && <p className="text-center text-gray-500">No more posts</p>}
      </div>
    </div>
  );
}
```

---

## 4. React Query Integration

```typescript
// hooks/usePosts.ts
'use client';

import { useInfiniteQuery } from '@tanstack/react-query';

async function fetchPosts({ pageParam = 1 }) {
  const res = await fetch(`/api/posts?page=${pageParam}&per_page=20`);
  return res.json();
}

export function usePosts() {
  return useInfiniteQuery({
    queryKey: ['posts'],
    queryFn: fetchPosts,
    getNextPageParam: (lastPage) =>
      lastPage.meta.next_page ?? undefined,
    initialPageParam: 1,
  });
}

// Component
export function PostListWithQuery() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = usePosts();

  const posts = data?.pages.flatMap((page) => page.data) ?? [];

  return (
    <div>
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}

      {hasNextPage && (
        <button
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
        >
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

---

## 5. API Route with Pagination

```typescript
// app/api/posts/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { posts } from '@/lib/db/schema';
import { desc, count } from 'drizzle-orm';

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const page = Number(searchParams.get('page')) || 1;
  const perPage = Math.min(Number(searchParams.get('per_page')) || 20, 100);
  const offset = (page - 1) * perPage;

  const [data, [{ total }]] = await Promise.all([
    db.query.posts.findMany({
      orderBy: [desc(posts.createdAt)],
      limit: perPage,
      offset,
    }),
    db.select({ total: count() }).from(posts),
  ]);

  const totalPages = Math.ceil(total / perPage);

  return NextResponse.json({
    data,
    meta: {
      current_page: page,
      per_page: perPage,
      total_pages: totalPages,
      total_count: total,
      next_page: page < totalPages ? page + 1 : null,
      prev_page: page > 1 ? page - 1 : null,
    },
  });
}
```

---

## 6. Parallel Data Fetching

```typescript
// app/posts/page.tsx
import { Suspense } from 'react';
import { getPosts, getPostStats } from '@/lib/data/posts';

export default async function PostsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const params = await searchParams;
  const page = Number(params.page) || 1;

  // Fetch in parallel
  const [postsData, stats] = await Promise.all([
    getPosts({ page }),
    getPostStats(),
  ]);

  return (
    <div>
      <Stats data={stats} />
      <PostList posts={postsData.posts} />
      <Pagination
        currentPage={page}
        totalPages={postsData.totalPages}
        baseUrl="/posts"
      />
    </div>
  );
}
```

---

## 7. Loading States

```typescript
// app/posts/loading.tsx
import { Skeleton } from '@/components/ui/Skeleton';

export default function PostsLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-32" />

      <div className="space-y-4">
        {Array.from({ length: 10 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>

      <div className="flex justify-center gap-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-10" />
        ))}
      </div>
    </div>
  );
}
```

---

## 8. SEO Considerations

```typescript
// app/posts/page.tsx
import type { Metadata } from 'next';

type Props = {
  searchParams: Promise<{ page?: string }>;
};

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const params = await searchParams;
  const page = Number(params.page) || 1;

  return {
    title: page === 1 ? 'Posts' : `Posts - Page ${page}`,
    alternates: {
      canonical: page === 1 ? '/posts' : `/posts?page=${page}`,
    },
    robots: page > 1 ? { index: false } : undefined,
  };
}
```

---

## 9. Testing Pagination

```typescript
// __tests__/pagination.test.tsx
import { render, screen } from '@testing-library/react';
import { Pagination } from '@/components/ui/Pagination';

describe('Pagination', () => {
  it('renders page numbers', () => {
    render(
      <Pagination currentPage={1} totalPages={5} baseUrl="/posts" />
    );

    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('disables previous on first page', () => {
    render(
      <Pagination currentPage={1} totalPages={5} baseUrl="/posts" />
    );

    const prev = screen.getByLabelText('Previous page');
    expect(prev).toHaveClass('cursor-not-allowed');
  });

  it('disables next on last page', () => {
    render(
      <Pagination currentPage={5} totalPages={5} baseUrl="/posts" />
    );

    const next = screen.getByLabelText('Next page');
    expect(next).toHaveClass('cursor-not-allowed');
  });
});
```
