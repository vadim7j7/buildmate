# Next.js Testing Patterns

Testing patterns and conventions for React + Next.js applications using Jest and
React Testing Library. All agents must follow these patterns when writing tests.

---

## 1. Test File Organization

```
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx      # Component unit test
│   │   └── index.ts
│   └── ...
├── containers/
│   ├── UserListContainer/
│   │   ├── UserListContainer.tsx
│   │   ├── UserListContainer.test.tsx
│   │   └── index.ts
├── services/
│   ├── users.ts
│   └── users.test.ts           # Service unit test
├── hooks/
│   ├── useAuth.ts
│   └── useAuth.test.ts         # Hook test
└── __tests__/
    ├── integration/            # Integration tests
    │   └── checkout.test.tsx
    └── e2e/                    # Playwright E2E tests
        └── auth.spec.ts
```

---

## 2. Component Testing

### Basic Component Test

```typescript
// components/Button/Button.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);

    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const handleClick = jest.fn();
    const user = userEvent.setup();

    render(<Button onClick={handleClick}>Click me</Button>);
    await user.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when loading', () => {
    render(<Button loading>Submit</Button>);

    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('shows loading spinner when loading', () => {
    render(<Button loading>Submit</Button>);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});
```

### Testing with Mantine

```typescript
// test-utils/render.tsx
import { render, RenderOptions } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

function AllProviders({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <MantineProvider>
        {children}
      </MantineProvider>
    </QueryClientProvider>
  );
}

function customRender(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllProviders, ...options });
}

export * from '@testing-library/react';
export { customRender as render };
```

```typescript
// components/ProjectCard/ProjectCard.test.tsx
import { render, screen } from '@/test-utils/render';
import userEvent from '@testing-library/user-event';
import { ProjectCard } from './ProjectCard';

const mockProject = {
  id: '1',
  name: 'Test Project',
  description: 'A test project description',
  status: 'active' as const,
};

describe('ProjectCard', () => {
  it('displays project information', () => {
    render(<ProjectCard project={mockProject} />);

    expect(screen.getByText('Test Project')).toBeInTheDocument();
    expect(screen.getByText('A test project description')).toBeInTheDocument();
  });

  it('calls onEdit when edit button clicked', async () => {
    const handleEdit = jest.fn();
    const user = userEvent.setup();

    render(<ProjectCard project={mockProject} onEdit={handleEdit} />);
    await user.click(screen.getByRole('button', { name: /edit/i }));

    expect(handleEdit).toHaveBeenCalledWith('1');
  });

  it('shows delete confirmation modal', async () => {
    const user = userEvent.setup();

    render(<ProjectCard project={mockProject} onDelete={jest.fn()} />);
    await user.click(screen.getByRole('button', { name: /delete/i }));

    expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
  });
});
```

---

## 3. Form Testing

```typescript
// components/CreateProjectForm/CreateProjectForm.test.tsx
import { render, screen, waitFor } from '@/test-utils/render';
import userEvent from '@testing-library/user-event';
import { CreateProjectForm } from './CreateProjectForm';

describe('CreateProjectForm', () => {
  it('submits form with valid data', async () => {
    const handleSubmit = jest.fn();
    const user = userEvent.setup();

    render(<CreateProjectForm onSubmit={handleSubmit} />);

    await user.type(screen.getByLabelText(/name/i), 'New Project');
    await user.type(screen.getByLabelText(/description/i), 'Project description');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledWith({
        name: 'New Project',
        description: 'Project description',
      });
    });
  });

  it('shows validation errors for empty name', async () => {
    const user = userEvent.setup();

    render(<CreateProjectForm onSubmit={jest.fn()} />);

    await user.click(screen.getByRole('button', { name: /create/i }));

    expect(await screen.findByText(/name is required/i)).toBeInTheDocument();
  });

  it('disables submit button while submitting', async () => {
    const handleSubmit = jest.fn(() => new Promise(() => {}));  // Never resolves
    const user = userEvent.setup();

    render(<CreateProjectForm onSubmit={handleSubmit} />);

    await user.type(screen.getByLabelText(/name/i), 'Test');
    await user.click(screen.getByRole('button', { name: /create/i }));

    expect(screen.getByRole('button', { name: /create/i })).toBeDisabled();
  });

  it('shows error notification on submit failure', async () => {
    const handleSubmit = jest.fn().mockRejectedValue(new Error('Server error'));
    const user = userEvent.setup();

    render(<CreateProjectForm onSubmit={handleSubmit} />);

    await user.type(screen.getByLabelText(/name/i), 'Test');
    await user.click(screen.getByRole('button', { name: /create/i }));

    expect(await screen.findByText(/failed to create project/i)).toBeInTheDocument();
  });
});
```

---

## 4. React Query Testing

```typescript
// containers/UserListContainer/UserListContainer.test.tsx
import { render, screen, waitFor } from '@/test-utils/render';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { UserListContainer } from './UserListContainer';

const mockUsers = [
  { id: '1', name: 'John Doe', email: 'john@example.com' },
  { id: '2', name: 'Jane Smith', email: 'jane@example.com' },
];

const server = setupServer(
  rest.get('/api/users', (req, res, ctx) => {
    return res(ctx.json({ data: mockUsers }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('UserListContainer', () => {
  it('shows loading state initially', () => {
    render(<UserListContainer />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('displays users after loading', async () => {
    render(<UserListContainer />);

    expect(await screen.findByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
  });

  it('shows error message on fetch failure', async () => {
    server.use(
      rest.get('/api/users', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Server error' }));
      })
    );

    render(<UserListContainer />);

    expect(await screen.findByText(/failed to load users/i)).toBeInTheDocument();
  });

  it('shows empty state when no users', async () => {
    server.use(
      rest.get('/api/users', (req, res, ctx) => {
        return res(ctx.json({ data: [] }));
      })
    );

    render(<UserListContainer />);

    expect(await screen.findByText(/no users found/i)).toBeInTheDocument();
  });
});
```

---

## 5. Hook Testing

```typescript
// hooks/useAuth.test.ts
import { renderHook, act, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { useAuth, AuthProvider } from './useAuth';

const server = setupServer(
  rest.post('/api/login', (req, res, ctx) => {
    return res(ctx.json({ user: { id: '1', email: 'test@example.com' } }));
  }),
  rest.post('/api/logout', (req, res, ctx) => {
    return res(ctx.json({ success: true }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe('useAuth', () => {
  it('returns unauthenticated state initially', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('authenticates user on login', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login({ email: 'test@example.com', password: 'password' });
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.email).toBe('test@example.com');
  });

  it('clears user on logout', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login({ email: 'test@example.com', password: 'password' });
    });

    expect(result.current.isAuthenticated).toBe(true);

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('handles login failure', async () => {
    server.use(
      rest.post('/api/login', (req, res, ctx) => {
        return res(ctx.status(401), ctx.json({ error: 'Invalid credentials' }));
      })
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await expect(
      act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'wrong' });
      })
    ).rejects.toThrow('Invalid credentials');

    expect(result.current.isAuthenticated).toBe(false);
  });
});
```

---

## 6. API Service Testing

```typescript
// services/projects.test.ts
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import {
  fetchProjects,
  createProject,
  updateProject,
  deleteProject,
} from './projects';

const mockProjects = [
  { id: '1', name: 'Project A' },
  { id: '2', name: 'Project B' },
];

const server = setupServer(
  rest.get('/api/projects', (req, res, ctx) => {
    const status = req.url.searchParams.get('status');
    if (status) {
      return res(ctx.json({ data: mockProjects.filter(() => true) }));
    }
    return res(ctx.json({ data: mockProjects }));
  }),

  rest.post('/api/projects', async (req, res, ctx) => {
    const body = await req.json();
    return res(ctx.json({ id: '3', ...body }));
  }),

  rest.put('/api/projects/:id', async (req, res, ctx) => {
    const body = await req.json();
    return res(ctx.json({ id: req.params.id, ...body }));
  }),

  rest.delete('/api/projects/:id', (req, res, ctx) => {
    return res(ctx.status(204));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('projects service', () => {
  describe('fetchProjects', () => {
    it('fetches all projects', async () => {
      const result = await fetchProjects();

      expect(result.data).toHaveLength(2);
      expect(result.data[0].name).toBe('Project A');
    });

    it('passes filters as query params', async () => {
      const result = await fetchProjects({ status: 'active' });

      expect(result.data).toBeDefined();
    });
  });

  describe('createProject', () => {
    it('creates a new project', async () => {
      const result = await createProject({ name: 'New Project' });

      expect(result.id).toBe('3');
      expect(result.name).toBe('New Project');
    });
  });

  describe('updateProject', () => {
    it('updates an existing project', async () => {
      const result = await updateProject('1', { name: 'Updated' });

      expect(result.id).toBe('1');
      expect(result.name).toBe('Updated');
    });
  });

  describe('deleteProject', () => {
    it('deletes a project', async () => {
      await expect(deleteProject('1')).resolves.not.toThrow();
    });
  });
});
```

---

## 7. Integration Testing

```typescript
// __tests__/integration/checkout.test.tsx
import { render, screen, waitFor } from '@/test-utils/render';
import userEvent from '@testing-library/user-event';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import CheckoutPage from '@/app/checkout/page';

const mockCart = {
  items: [
    { id: '1', name: 'Product A', price: 1000, quantity: 2 },
    { id: '2', name: 'Product B', price: 500, quantity: 1 },
  ],
  total: 2500,
};

const server = setupServer(
  rest.get('/api/cart', (req, res, ctx) => {
    return res(ctx.json(mockCart));
  }),
  rest.post('/api/orders', async (req, res, ctx) => {
    return res(ctx.json({ orderId: 'ORD-123' }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Checkout Flow', () => {
  it('completes checkout successfully', async () => {
    const user = userEvent.setup();

    render(<CheckoutPage />);

    // Wait for cart to load
    expect(await screen.findByText('Product A')).toBeInTheDocument();
    expect(screen.getByText('$25.00')).toBeInTheDocument();  // Total

    // Fill shipping form
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.type(screen.getByLabelText(/address/i), '123 Main St');
    await user.type(screen.getByLabelText(/city/i), 'New York');
    await user.type(screen.getByLabelText(/zip/i), '10001');

    // Submit order
    await user.click(screen.getByRole('button', { name: /place order/i }));

    // Verify success
    expect(await screen.findByText(/order confirmed/i)).toBeInTheDocument();
    expect(screen.getByText('ORD-123')).toBeInTheDocument();
  });

  it('shows error when payment fails', async () => {
    server.use(
      rest.post('/api/orders', (req, res, ctx) => {
        return res(ctx.status(402), ctx.json({ error: 'Payment declined' }));
      })
    );

    const user = userEvent.setup();

    render(<CheckoutPage />);

    // Fill form and submit
    await screen.findByText('Product A');
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.click(screen.getByRole('button', { name: /place order/i }));

    // Verify error
    expect(await screen.findByText(/payment declined/i)).toBeInTheDocument();
  });
});
```

---

## 8. Playwright E2E Tests

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('user can sign up', async ({ page }) => {
    await page.goto('/signup');

    await page.fill('[name="email"]', 'newuser@example.com');
    await page.fill('[name="password"]', 'SecurePassword123!');
    await page.fill('[name="confirmPassword"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('text=Welcome')).toBeVisible();
  });

  test('user can log in', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="email"]', 'existing@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
  });

  test('shows error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="email"]', 'wrong@example.com');
    await page.fill('[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('text=Invalid credentials')).toBeVisible();
    await expect(page).toHaveURL('/login');
  });

  test('user can log out', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[name="email"]', 'existing@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');

    // Log out
    await page.click('button[aria-label="User menu"]');
    await page.click('text=Log out');

    await expect(page).toHaveURL('/');
  });
});
```

---

## 9. Test Utilities

### Custom Matchers

```typescript
// test-utils/matchers.ts
expect.extend({
  toHaveBeenCalledWithMatch(received, expected) {
    const calls = received.mock.calls;
    const match = calls.some((call: unknown[]) =>
      Object.entries(expected).every(([key, value]) =>
        call[0][key] === value
      )
    );

    return {
      pass: match,
      message: () =>
        `expected ${received} to have been called with matching ${JSON.stringify(expected)}`,
    };
  },
});

// Usage
expect(mockFn).toHaveBeenCalledWithMatch({ id: '1' });
```

### Factory Functions

```typescript
// test-utils/factories.ts
export function createUser(overrides: Partial<User> = {}): User {
  return {
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
    createdAt: new Date().toISOString(),
    ...overrides,
  };
}

export function createProject(overrides: Partial<Project> = {}): Project {
  return {
    id: '1',
    name: 'Test Project',
    description: 'A test project',
    status: 'active',
    userId: '1',
    createdAt: new Date().toISOString(),
    ...overrides,
  };
}

// Usage
const user = createUser({ name: 'Custom Name' });
const project = createProject({ status: 'archived' });
```

---

## 10. Common Patterns

### Testing Loading States

```typescript
it('shows loading state', () => {
  render(<UserList />);
  expect(screen.getByRole('progressbar')).toBeInTheDocument();
});
```

### Testing Error States

```typescript
it('shows error message on failure', async () => {
  server.use(
    rest.get('/api/users', (req, res, ctx) => res(ctx.status(500)))
  );

  render(<UserList />);

  expect(await screen.findByText(/error/i)).toBeInTheDocument();
});
```

### Testing Empty States

```typescript
it('shows empty state when no data', async () => {
  server.use(
    rest.get('/api/users', (req, res, ctx) => res(ctx.json({ data: [] })))
  );

  render(<UserList />);

  expect(await screen.findByText(/no users/i)).toBeInTheDocument();
});
```

---

## Quick Reference

| Test Type | Tool | Location |
|-----------|------|----------|
| Component unit | Jest + RTL | `*.test.tsx` |
| Hook testing | `renderHook` | `hooks/*.test.ts` |
| API mocking | MSW | All tests |
| Integration | Jest + RTL | `__tests__/integration/` |
| E2E | Playwright | `e2e/*.spec.ts` |

### Query Priority

```typescript
// Preferred order (most accessible first)
screen.getByRole('button', { name: /submit/i })
screen.getByLabelText(/email/i)
screen.getByPlaceholderText(/search/i)
screen.getByText(/welcome/i)
screen.getByTestId('custom-element')  // Last resort
```

### Async Queries

```typescript
// Wait for element to appear
await screen.findByText(/loaded/i)

// Wait for element to disappear
await waitFor(() => {
  expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
})

// Wait for condition
await waitFor(() => {
  expect(mockFn).toHaveBeenCalled()
})
```
