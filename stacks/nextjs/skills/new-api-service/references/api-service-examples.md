# API Service Examples

## Base Request Wrapper

The foundation for all API services. Provides typed HTTP requests with
consistent error handling.

```typescript
// src/services/request.ts

type RequestOptions = RequestInit & {
  params?: Record<string, string | number | boolean | undefined>;
};

/**
 * Type-safe HTTP request wrapper.
 * All API services use this function for consistent request handling.
 */
export async function request<T>(url: string, options?: RequestOptions): Promise<T> {
  // Append query params if provided
  let fullUrl = url;
  if (options?.params) {
    const searchParams = new URLSearchParams();
    Object.entries(options.params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      fullUrl += `?${queryString}`;
    }
  }

  const { params, ...fetchOptions } = options ?? {};

  const response = await fetch(fullUrl, {
    headers: {
      'Content-Type': 'application/json',
      ...fetchOptions?.headers,
    },
    ...fetchOptions,
  });

  if (!response.ok) {
    const errorBody = await response.text().catch(() => '');
    throw new ApiError(response.status, errorBody || `Request failed: ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/**
 * Custom error class for API errors with status code.
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
```

---

## Example 1: Projects Service (Full CRUD)

```typescript
// src/services/projects.ts
import { request } from './request';

// --- Types ---

type Project = {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'archived' | 'draft';
  ownerId: string;
  createdAt: string;
  updatedAt: string;
};

type CreateProjectPayload = {
  name: string;
  description: string;
};

type UpdateProjectPayload = {
  name?: string;
  description?: string;
  status?: 'active' | 'archived' | 'draft';
};

type ProjectListParams = {
  page?: number;
  perPage?: number;
  status?: string;
  query?: string;
};

type PaginatedResponse<T> = {
  data: T[];
  total: number;
  page: number;
  perPage: number;
  totalPages: number;
};

// --- API Functions ---

/** Fetch paginated list of projects with optional filters */
export const fetchProjectsApi = (params?: ProjectListParams) =>
  request<PaginatedResponse<Project>>('/api/projects', { params });

/** Fetch a single project by ID */
export const fetchProjectApi = (id: string) =>
  request<Project>(`/api/projects/${id}`);

/** Create a new project */
export const createProjectApi = (data: CreateProjectPayload) =>
  request<Project>('/api/projects', {
    method: 'POST',
    body: JSON.stringify(data),
  });

/** Update an existing project */
export const updateProjectApi = (id: string, data: UpdateProjectPayload) =>
  request<Project>(`/api/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

/** Delete a project */
export const deleteProjectApi = (id: string) =>
  request<void>(`/api/projects/${id}`, {
    method: 'DELETE',
  });

/** Archive a project (convenience wrapper) */
export const archiveProjectApi = (id: string) =>
  updateProjectApi(id, { status: 'archived' });
```

---

## Example 2: Users Service

```typescript
// src/services/users.ts
import { request } from './request';

type User = {
  id: string;
  name: string;
  email: string;
  avatarUrl: string | null;
  role: 'admin' | 'member' | 'viewer';
  createdAt: string;
};

type UpdateUserPayload = {
  name?: string;
  email?: string;
  avatarUrl?: string | null;
};

type InviteUserPayload = {
  email: string;
  role: 'member' | 'viewer';
};

/** Fetch the current authenticated user's profile */
export const fetchCurrentUserApi = () =>
  request<User>('/api/users/me');

/** Update the current user's profile */
export const updateCurrentUserApi = (data: UpdateUserPayload) =>
  request<User>('/api/users/me', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

/** Fetch a user by ID */
export const fetchUserApi = (id: string) =>
  request<User>(`/api/users/${id}`);

/** Fetch all users in the workspace */
export const fetchUsersApi = () =>
  request<User[]>('/api/users');

/** Invite a new user to the workspace */
export const inviteUserApi = (data: InviteUserPayload) =>
  request<User>('/api/users/invite', {
    method: 'POST',
    body: JSON.stringify(data),
  });

/** Remove a user from the workspace */
export const removeUserApi = (id: string) =>
  request<void>(`/api/users/${id}`, {
    method: 'DELETE',
  });
```

---

## Example 3: Auth Service

```typescript
// src/services/auth.ts
import { request } from './request';

type LoginPayload = {
  email: string;
  password: string;
};

type RegisterPayload = {
  name: string;
  email: string;
  password: string;
};

type AuthResponse = {
  user: {
    id: string;
    name: string;
    email: string;
  };
  token: string;
};

type ForgotPasswordPayload = {
  email: string;
};

type ResetPasswordPayload = {
  token: string;
  password: string;
};

/** Authenticate with email and password */
export const loginApi = (data: LoginPayload) =>
  request<AuthResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });

/** Register a new account */
export const registerApi = (data: RegisterPayload) =>
  request<AuthResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });

/** End the current session */
export const logoutApi = () =>
  request<void>('/api/auth/logout', {
    method: 'POST',
  });

/** Request a password reset email */
export const forgotPasswordApi = (data: ForgotPasswordPayload) =>
  request<{ message: string }>('/api/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify(data),
  });

/** Reset password with token */
export const resetPasswordApi = (data: ResetPasswordPayload) =>
  request<{ message: string }>('/api/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify(data),
  });

/** Verify email with token */
export const verifyEmailApi = (token: string) =>
  request<{ message: string }>('/api/auth/verify-email', {
    method: 'POST',
    body: JSON.stringify({ token }),
  });
```

---

## Example 4: Service Test File

```typescript
// src/services/projects.test.ts
import {
  fetchProjectsApi,
  fetchProjectApi,
  createProjectApi,
  updateProjectApi,
  deleteProjectApi,
} from './projects';

// Mock global fetch
global.fetch = jest.fn();
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

function mockJsonResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
  } as Response;
}

describe('projects service', () => {
  afterEach(() => {
    mockFetch.mockReset();
  });

  describe('fetchProjectsApi', () => {
    it('fetches projects with default params', async () => {
      const data = { data: [], total: 0, page: 1, perPage: 20, totalPages: 0 };
      mockFetch.mockResolvedValue(mockJsonResponse(data));

      const result = await fetchProjectsApi();

      expect(result).toEqual(data);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/projects',
        expect.objectContaining({
          headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        })
      );
    });

    it('appends query params', async () => {
      mockFetch.mockResolvedValue(mockJsonResponse({ data: [] }));

      await fetchProjectsApi({ page: 2, status: 'active' });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('page=2'),
        expect.any(Object)
      );
    });
  });

  describe('fetchProjectApi', () => {
    it('fetches a single project by ID', async () => {
      const project = { id: '1', name: 'Test', description: '' };
      mockFetch.mockResolvedValue(mockJsonResponse(project));

      const result = await fetchProjectApi('1');

      expect(result).toEqual(project);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/projects/1',
        expect.any(Object)
      );
    });

    it('throws on 404', async () => {
      mockFetch.mockResolvedValue(mockJsonResponse({ error: 'Not found' }, 404));

      await expect(fetchProjectApi('999')).rejects.toThrow();
    });
  });

  describe('createProjectApi', () => {
    it('sends POST with body', async () => {
      const payload = { name: 'New', description: 'Desc' };
      const created = { id: '1', ...payload, status: 'draft', createdAt: '', updatedAt: '', ownerId: 'u1' };
      mockFetch.mockResolvedValue(mockJsonResponse(created, 201));

      const result = await createProjectApi(payload);

      expect(result).toEqual(created);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/projects',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(payload),
        })
      );
    });
  });

  describe('updateProjectApi', () => {
    it('sends PATCH with partial body', async () => {
      const payload = { name: 'Updated' };
      mockFetch.mockResolvedValue(mockJsonResponse({ id: '1', name: 'Updated' }));

      await updateProjectApi('1', payload);

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/projects/1',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(payload),
        })
      );
    });
  });

  describe('deleteProjectApi', () => {
    it('sends DELETE request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
        json: async () => undefined,
        text: async () => '',
      } as Response);

      await deleteProjectApi('1');

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/projects/1',
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });
});
```
