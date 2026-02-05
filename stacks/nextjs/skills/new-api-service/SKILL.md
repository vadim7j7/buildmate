---
name: new-api-service
description: Generate a new API service module with typed request functions
---

# /new-api-service

## What This Does

Creates a new API service module in `src/services/` with typed request functions
following the `request<T>()` wrapper pattern. All exported functions use the
`Api` suffix convention.

## Usage

```
/new-api-service projects
/new-api-service users
/new-api-service auth
/new-api-service notifications
```

## How It Works

### 1. Determine CRUD Operations

Based on the resource name, generate standard CRUD operations:

| Operation | Function Name | HTTP Method | Endpoint |
|---|---|---|---|
| List | `fetch<Resource>sApi()` | GET | `/api/<resources>` |
| Get | `fetch<Resource>Api(id)` | GET | `/api/<resources>/:id` |
| Create | `create<Resource>Api(data)` | POST | `/api/<resources>` |
| Update | `update<Resource>Api(id, data)` | PATCH | `/api/<resources>/:id` |
| Delete | `delete<Resource>Api(id)` | DELETE | `/api/<resources>/:id` |

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` for conventions
- `skills/new-api-service/references/api-service-examples.md` for examples
- `src/services/request.ts` for the base request wrapper
- Existing services in `src/services/` for project patterns

### 3. Generate Files

#### Service: `src/services/<resource>.ts`

```typescript
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
  request<<Resource>[]>('/api/<resources>');

export const fetch<Resource>Api = (id: string) =>
  request<<Resource>>(`/api/<resources>/${id}`);

export const create<Resource>Api = (data: Create<Resource>Payload) =>
  request<<Resource>>('/api/<resources>', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const update<Resource>Api = (id: string, data: Update<Resource>Payload) =>
  request<<Resource>>(`/api/<resources>/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

export const delete<Resource>Api = (id: string) =>
  request<void>(`/api/<resources>/${id}`, { method: 'DELETE' });
```

#### Test: `src/services/<resource>.test.ts`

Tests for each API function with mocked fetch.

### 4. Create Request Wrapper (if missing)

If `src/services/request.ts` does not exist, create it:

```typescript
export async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
```

### 5. Verify

Run `npx tsc --noEmit` to verify types are correct.

## Rules

- All functions use the `Api` suffix: `fetchProjectsApi`, `createProjectApi`
- All functions use `request<T>()` wrapper for type safety
- Response types are explicitly defined (no `any`)
- Request payloads are typed
- Named exports (no default export)
- Use `type` (not `interface`) for all type definitions

## Output

```
Created:
  src/services/<resource>.ts       -- API service functions
  src/services/<resource>.test.ts  -- Unit tests
  src/services/request.ts          -- Base request wrapper (if missing)

Verified:
  npx tsc --noEmit  -- PASS
```
