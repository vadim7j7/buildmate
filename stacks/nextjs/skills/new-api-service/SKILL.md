---
name: new-api-service
description: Generate a server-only API client module with typed request functions for an external backend
---

# /new-api-service

## What This Does

Creates a **server-only** API client module in `src/services/` with typed request
functions for an external backend (e.g. the Rails/Django/Express API next to this app).
All exported functions use the `Api` suffix convention.

These functions run on the server only. They are called from:
- data functions in `src/lib/data/` (wrapped in `cache()`), which async Server
  Component pages `await`;
- Server Actions in `src/lib/actions/` for mutations.

They are **not** called from Client Components with `useEffect`. If the app has no
external backend (it talks to its own database), skip this skill: put queries in
`src/lib/data/` and mutations in Server Actions (`/new-server-action`).

## Usage

```
/new-api-service projects
/new-api-service users
/new-api-service notifications
```

## How It Works

### 1. Determine CRUD Operations

| Operation | Function Name | HTTP Method | Endpoint (relative to `API_URL`) |
|---|---|---|---|
| List | `fetch<Resource>sApi()` | GET | `/<resources>` |
| Get | `fetch<Resource>Api(id)` | GET | `/<resources>/:id` |
| Create | `create<Resource>Api(data)` | POST | `/<resources>` |
| Update | `update<Resource>Api(id, data)` | PATCH | `/<resources>/:id` |
| Delete | `delete<Resource>Api(id)` | DELETE | `/<resources>/:id` |

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` for conventions
- `skills/new-api-service/references/api-service-examples.md` for examples
- `src/services/request.ts` for the base request wrapper
- Existing services in `src/services/` and data functions in `src/lib/data/`

### 3. Generate Files

#### Service: `src/services/<resource>.ts`

```typescript
import 'server-only';
import { request } from './request';

type <Resource> = {
  id: string;
  // typed fields
};

type Create<Resource>Payload = {
  // create fields
};

type Update<Resource>Payload = Partial<Create<Resource>Payload>;

export const fetch<Resource>sApi = () =>
  request<<Resource>[]>('/<resources>');

export const fetch<Resource>Api = (id: string) =>
  request<<Resource>>(`/<resources>/${id}`);

export const create<Resource>Api = (data: Create<Resource>Payload) =>
  request<<Resource>>('/<resources>', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const update<Resource>Api = (id: string, data: Update<Resource>Payload) =>
  request<<Resource>>(`/<resources>/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

export const delete<Resource>Api = (id: string) =>
  request<void>(`/<resources>/${id}`, { method: 'DELETE' });
```

#### Data functions: `src/lib/data/<resource>.ts`

Reads used by pages go through a `cache()`-wrapped data function so one request
dedupes repeated calls (e.g. `generateMetadata` + the page):

```typescript
import 'server-only';
import { cache } from 'react';
import { fetch<Resource>sApi, fetch<Resource>Api } from '@/services/<resource>';

export const get<Resource>s = cache(() => fetch<Resource>sApi());
export const get<Resource> = cache((id: string) => fetch<Resource>Api(id));
```

Mutations (`create/update/delete...Api`) are called from Server Actions, which
authenticate, authorize and validate input first (see `/new-server-action`).

#### Test: `src/services/<resource>.test.ts`

Tests for each API function with mocked `fetch` (and `server-only` mocked, see examples).

### 4. Create Request Wrapper (if missing)

If `src/services/request.ts` does not exist, create it:

```typescript
import 'server-only';
import { getAccessToken } from '@/lib/session'; // reads the session cookie via next/headers

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = await getAccessToken();
  const response = await fetch(`${process.env.API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
```

`API_URL` is a server env var (no `NEXT_PUBLIC_` prefix): the backend URL and the
token never reach the browser.

### 5. Verify

Run `npx tsc --noEmit` to verify types are correct.

## Rules

- Every service file starts with `import 'server-only'`
- All functions use the `Api` suffix: `fetchProjectsApi`, `createProjectApi`
- All functions use the `request<T>()` wrapper for type safety
- Response types are explicitly defined (no `any`)
- Request payloads are typed
- Named exports (no default export)
- Use `type` (not `interface`) for all type definitions
- Never import a service from a `'use client'` file; pass data down as props instead

## Output

```
Created:
  src/services/<resource>.ts       -- Server-only API functions
  src/lib/data/<resource>.ts       -- cache()-wrapped reads for pages
  src/services/<resource>.test.ts  -- Unit tests
  src/services/request.ts          -- Base request wrapper (if missing)

Verified:
  npx tsc --noEmit  -- PASS
```
