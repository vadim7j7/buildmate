# Next.js Common Pitfalls & Anti-Patterns

Common mistakes and performance issues in React + Next.js applications. All agents
must recognize and avoid these patterns.

---

## 1. Hydration Errors

The most common Next.js issue. Occurs when server HTML doesn't match client render.

```typescript
// WRONG - different output on server vs client
function Greeting() {
  return <p>Hello, it's {new Date().toLocaleTimeString()}</p>;
}

// Server renders: "Hello, it's 10:00:00 AM"
// Client renders: "Hello, it's 10:00:01 AM"
// Hydration mismatch!

// CORRECT - use useEffect for client-only values
function Greeting() {
  const [time, setTime] = useState<string | null>(null);

  useEffect(() => {
    setTime(new Date().toLocaleTimeString());
  }, []);

  return <p>Hello, {time ? `it's ${time}` : '...'}</p>;
}

// CORRECT - suppressHydrationWarning for unavoidable cases
<time suppressHydrationWarning>
  {new Date().toLocaleTimeString()}
</time>
```

### Common Hydration Mismatch Causes

```typescript
// WRONG - using window/localStorage in render
function Theme() {
  const theme = localStorage.getItem('theme');  // Error on server!
  return <div data-theme={theme}>...</div>;
}

// CORRECT - check for client
function Theme() {
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    const saved = localStorage.getItem('theme');
    if (saved) setTheme(saved);
  }, []);

  return <div data-theme={theme}>...</div>;
}

// WRONG - conditional rendering based on window size
function Layout() {
  if (window.innerWidth < 768) {  // Error on server!
    return <MobileLayout />;
  }
  return <DesktopLayout />;
}

// CORRECT - use CSS or useEffect
function Layout() {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return isMobile ? <MobileLayout /> : <DesktopLayout />;
}
```

---

## 2. React Query Pitfalls

### Stale Closure

```typescript
// WRONG - stale closure in callback
function UserProfile({ userId }: { userId: string }) {
  const [count, setCount] = useState(0);

  const { data } = useQuery({
    queryKey: ['user', userId],
    queryFn: async () => {
      console.log(count);  // Always logs initial value!
      return fetchUser(userId);
    },
  });
}

// CORRECT - include in dependency or use ref
function UserProfile({ userId }: { userId: string }) {
  const [count, setCount] = useState(0);

  const { data } = useQuery({
    queryKey: ['user', userId, count],  // Include in queryKey
    queryFn: async () => {
      console.log(count);  // Now gets current value
      return fetchUser(userId);
    },
  });
}
```

### Missing Query Keys

```typescript
// WRONG - same queryKey for different data
const { data: user } = useQuery({
  queryKey: ['user'],
  queryFn: () => fetchUser(userId),  // userId not in key!
});

// When userId changes, stale data is shown

// CORRECT - include all variables in queryKey
const { data: user } = useQuery({
  queryKey: ['user', userId],
  queryFn: () => fetchUser(userId),
});
```

### Infinite Refetches

```typescript
// WRONG - queryFn changes every render
const { data } = useQuery({
  queryKey: ['data'],
  queryFn: async () => {
    const options = { filter };  // New object every render
    return fetchData(options);
  },
});

// CORRECT - memoize or use stable references
const queryFn = useCallback(async () => {
  return fetchData({ filter });
}, [filter]);

const { data } = useQuery({
  queryKey: ['data', filter],
  queryFn,
});
```

### Mutation Invalidation Missing

```typescript
// WRONG - data stale after mutation
const createUser = useMutation({
  mutationFn: (data: UserCreate) => createUserApi(data),
});

// After mutation, user list still shows old data

// CORRECT - invalidate related queries
const queryClient = useQueryClient();

const createUser = useMutation({
  mutationFn: (data: UserCreate) => createUserApi(data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['users'] });
  },
});
```

---

## 3. Server Component vs Client Component Confusion

### Using Hooks in Server Components

```typescript
// WRONG - hooks in server component
// app/page.tsx (Server Component by default)
export default function Page() {
  const [count, setCount] = useState(0);  // Error!
  return <div>{count}</div>;
}

// CORRECT - add 'use client' directive
'use client';

export default function Page() {
  const [count, setCount] = useState(0);
  return <div>{count}</div>;
}

// BETTER - keep page as server, extract client part
// app/page.tsx
import { Counter } from '@/components/Counter';

export default function Page() {
  return <Counter />;  // Counter is 'use client'
}
```

### Passing Functions to Client Components

```typescript
// WRONG - passing function from server to client
// app/page.tsx (Server Component)
export default function Page() {
  const handleClick = () => console.log('clicked');
  return <ClientButton onClick={handleClick} />;  // Error!
}

// CORRECT - define handler in client component
// components/ClientButton.tsx
'use client';

export function ClientButton() {
  const handleClick = () => console.log('clicked');
  return <button onClick={handleClick}>Click</button>;
}
```

### Serialization Limits

```typescript
// WRONG - passing non-serializable props
// app/page.tsx
export default function Page() {
  const user = await getUser();
  return <ClientComponent date={user.createdAt} />;  // Date object!
}

// CORRECT - serialize first
export default function Page() {
  const user = await getUser();
  return <ClientComponent createdAt={user.createdAt.toISOString()} />;
}
```

---

## 4. Layout and Data Fetching Issues

### Fetching in Layouts

```typescript
// WRONG - fetching user in layout causes waterfalls
// app/layout.tsx
export default async function Layout({ children }) {
  const user = await getUser();  // Blocks all page renders
  return <div><Sidebar user={user} />{children}</div>;
}

// CORRECT - parallel fetching with loading states
// app/layout.tsx
export default function Layout({ children }) {
  return (
    <div>
      <Suspense fallback={<SidebarSkeleton />}>
        <Sidebar />
      </Suspense>
      {children}
    </div>
  );
}

// components/Sidebar.tsx
export default async function Sidebar() {
  const user = await getUser();  // Fetches in parallel with page
  return <nav>{user.name}</nav>;
}
```

### Not Using Suspense

```typescript
// WRONG - whole page blocked by slow fetch
// app/page.tsx
export default async function Page() {
  const posts = await getPosts();  // 3 second API call
  const sidebar = await getSidebar();  // 2 second API call
  // Page shows after 5 seconds (sequential)

  return <div>{/* ... */}</div>;
}

// CORRECT - parallel fetching with Suspense
export default async function Page() {
  return (
    <div>
      <Suspense fallback={<SidebarSkeleton />}>
        <Sidebar />
      </Suspense>
      <Suspense fallback={<PostsSkeleton />}>
        <Posts />
      </Suspense>
    </div>
  );
  // Page shows immediately with skeletons
  // Each section loads independently
}
```

---

## 5. Mantine / UI Library Issues

### Missing Provider

```typescript
// WRONG - using Mantine without provider
'use client';

import { Button } from '@mantine/core';

export default function Page() {
  return <Button>Click</Button>;  // Broken styling!
}

// CORRECT - wrap app in MantineProvider
// app/layout.tsx
import { MantineProvider } from '@mantine/core';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <MantineProvider>{children}</MantineProvider>
      </body>
    </html>
  );
}
```

### Form State Not Persisting

```typescript
// WRONG - form resets on every render
function MyForm() {
  const form = useForm({  // Creates new form every render
    initialValues: { name: '' },
  });

  const { data } = useQuery({ /* ... */ });

  return <form>{/* ... */}</form>;
}

// CORRECT - useForm is stable, but be careful with effects
function MyForm({ defaultValues }) {
  const form = useForm({
    initialValues: defaultValues,
  });

  // If you need to update from async data:
  useEffect(() => {
    if (data) {
      form.setValues(data);
    }
  }, [data]);
}
```

---

## 6. State Management Pitfalls

### Zustand Store Outside React

```typescript
// WRONG - accessing store outside React loses reactivity
import { useStore } from '@/stores/useStore';

const count = useStore.getState().count;  // One-time read, not reactive!

function Component() {
  return <div>{count}</div>;  // Never updates!
}

// CORRECT - use hook inside component
function Component() {
  const count = useStore((state) => state.count);
  return <div>{count}</div>;  // Reactive!
}
```

### Selecting Too Much State

```typescript
// WRONG - subscribes to entire store
function Component() {
  const store = useStore();  // Re-renders on ANY state change
  return <div>{store.count}</div>;
}

// CORRECT - select specific slice
function Component() {
  const count = useStore((state) => state.count);  // Only re-renders when count changes
  return <div>{count}</div>;
}

// CORRECT - multiple selectors
function Component() {
  const count = useStore((state) => state.count);
  const name = useStore((state) => state.name);
  return <div>{name}: {count}</div>;
}
```

---

## 7. Performance Anti-Patterns

### Inline Object/Array Props

```typescript
// WRONG - new object every render breaks memo
function Parent() {
  return <Child style={{ color: 'red' }} />;  // New object every render
}

const Child = memo(function Child({ style }) {
  return <div style={style}>Text</div>;  // memo doesn't help!
});

// CORRECT - stable reference
const style = { color: 'red' };

function Parent() {
  return <Child style={style} />;
}

// OR useMemo
function Parent() {
  const style = useMemo(() => ({ color: 'red' }), []);
  return <Child style={style} />;
}
```

### Missing useCallback

```typescript
// WRONG - new function every render
function Parent() {
  const handleClick = () => console.log('clicked');
  return <MemoizedChild onClick={handleClick} />;  // Memo broken!
}

// CORRECT - stable callback
function Parent() {
  const handleClick = useCallback(() => {
    console.log('clicked');
  }, []);
  return <MemoizedChild onClick={handleClick} />;
}
```

### Rendering Large Lists

```typescript
// WRONG - rendering 10,000 items at once
function List({ items }) {
  return (
    <ul>
      {items.map((item) => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  );
}

// CORRECT - virtualization
import { useVirtualizer } from '@tanstack/react-virtual';

function List({ items }) {
  const parentRef = useRef(null);
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 35,
  });

  return (
    <div ref={parentRef} style={{ height: 400, overflow: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div key={virtualItem.key} style={{
            position: 'absolute',
            top: 0,
            transform: `translateY(${virtualItem.start}px)`,
          }}>
            {items[virtualItem.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 8. API Route Issues

### Not Handling Errors

```typescript
// WRONG - unhandled errors crash the request
export async function GET() {
  const data = await fetchExternalApi();  // Could throw!
  return NextResponse.json(data);
}

// CORRECT - proper error handling
export async function GET() {
  try {
    const data = await fetchExternalApi();
    return NextResponse.json(data);
  } catch (error) {
    console.error('API fetch failed:', error);
    return NextResponse.json(
      { error: 'Failed to fetch data' },
      { status: 500 }
    );
  }
}
```

### Forgetting to Await

```typescript
// WRONG - not awaiting async operations
export async function POST(request: Request) {
  const body = request.json();  // Missing await!
  // body is a Promise, not the actual data

  db.insert(users).values(body);  // Missing await!
  // Insert might not complete before response

  return NextResponse.json({ success: true });
}

// CORRECT
export async function POST(request: Request) {
  const body = await request.json();
  await db.insert(users).values(body);
  return NextResponse.json({ success: true });
}
```

---

## 9. Image Optimization

```typescript
// WRONG - using regular img tag
<img src={user.avatarUrl} alt="Avatar" />

// CORRECT - use Next.js Image
import Image from 'next/image';

<Image
  src={user.avatarUrl}
  alt="Avatar"
  width={100}
  height={100}
/>

// WRONG - missing sizes for responsive images
<Image src={url} fill alt="Hero" />

// CORRECT - include sizes
<Image
  src={url}
  fill
  alt="Hero"
  sizes="(max-width: 768px) 100vw, 50vw"
/>
```

---

## 10. TypeScript Pitfalls

### Type Assertions Hiding Bugs

```typescript
// WRONG - unsafe type assertion
const user = data as User;  // Could be undefined!
console.log(user.name);  // Runtime error if undefined

// CORRECT - type guard
function isUser(data: unknown): data is User {
  return (
    typeof data === 'object' &&
    data !== null &&
    'name' in data &&
    typeof (data as User).name === 'string'
  );
}

if (isUser(data)) {
  console.log(data.name);  // Safe
}

// CORRECT - optional chaining for nullable data
const userName = data?.name ?? 'Unknown';
```

### Ignoring Return Types

```typescript
// WRONG - implicit any return
async function fetchUser(id: string) {
  const response = await fetch(`/api/users/${id}`);
  return response.json();  // Returns Promise<any>
}

// CORRECT - explicit return type
async function fetchUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  return response.json() as Promise<User>;
}

// BEST - validate with Zod
import { z } from 'zod';

const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string().email(),
});

async function fetchUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  const data = await response.json();
  return UserSchema.parse(data);  // Throws if invalid
}
```

---

## Quick Reference

| Problem | Solution |
|---------|----------|
| Hydration mismatch | useEffect for client-only values |
| React Query stale data | Include all deps in queryKey |
| Hooks in server component | Add 'use client' directive |
| Layout waterfall | Use Suspense and parallel fetching |
| Mantine broken styles | Add MantineProvider to layout |
| Zustand not reactive | Use hook inside component |
| Memo not working | Stable props with useMemo/useCallback |
| Large list lag | Use virtualization |
| API errors crash | Try/catch with proper error response |
| Type assertions | Use type guards instead |
