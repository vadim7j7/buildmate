# Jest + React Testing Library Patterns

## Setup

### Test Environment Configuration

```typescript
// jest.config.ts
import type { Config } from 'jest';
import nextJest from 'next/jest';

const createJestConfig = nextJest({ dir: './' });

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 85,
      statements: 85,
    },
  },
};

export default createJestConfig(config);
```

```typescript
// jest.setup.ts
import '@testing-library/jest-dom';
```

### Mantine Test Wrapper

Many Mantine components require the MantineProvider. Create a test utility:

```typescript
// src/test-utils/render.tsx
import { render, type RenderOptions } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { type ReactElement } from 'react';

function AllProviders({ children }: { children: React.ReactNode }) {
  return (
    <MantineProvider>
      <Notifications />
      {children}
    </MantineProvider>
  );
}

function customRender(ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
  return render(ui, { wrapper: AllProviders, ...options });
}

export * from '@testing-library/react';
export { customRender as render };
```

---

## Pattern 1: Component Render Tests

Verify a component renders without crashing and displays expected content.

```typescript
import { render, screen } from '@/test-utils/render';
import { ProjectCard } from './ProjectCard';

describe('ProjectCard', () => {
  const defaultProps = {
    name: 'My Project',
    description: 'A brief description',
    status: 'active' as const,
  };

  it('renders the project name', () => {
    render(<ProjectCard {...defaultProps} />);
    expect(screen.getByText('My Project')).toBeInTheDocument();
  });

  it('renders the description', () => {
    render(<ProjectCard {...defaultProps} />);
    expect(screen.getByText('A brief description')).toBeInTheDocument();
  });

  it('shows active badge for active projects', () => {
    render(<ProjectCard {...defaultProps} status="active" />);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('shows archived badge for archived projects', () => {
    render(<ProjectCard {...defaultProps} status="archived" />);
    expect(screen.getByText('Archived')).toBeInTheDocument();
  });

  it('handles missing description gracefully', () => {
    render(<ProjectCard {...defaultProps} description="" />);
    expect(screen.getByText('My Project')).toBeInTheDocument();
    expect(screen.queryByText('A brief description')).not.toBeInTheDocument();
  });
});
```

---

## Pattern 2: User Interaction Tests

Use `@testing-library/user-event` for realistic user interactions.

```typescript
import { render, screen, waitFor } from '@/test-utils/render';
import userEvent from '@testing-library/user-event';
import { SearchBar } from './SearchBar';

describe('SearchBar', () => {
  it('calls onSearch when user types and submits', async () => {
    const user = userEvent.setup();
    const onSearch = jest.fn();

    render(<SearchBar onSearch={onSearch} />);

    const input = screen.getByPlaceholderText(/search/i);
    await user.type(input, 'react');
    await user.keyboard('{Enter}');

    expect(onSearch).toHaveBeenCalledWith('react');
  });

  it('clears input when clear button is clicked', async () => {
    const user = userEvent.setup();
    render(<SearchBar onSearch={jest.fn()} />);

    const input = screen.getByPlaceholderText(/search/i);
    await user.type(input, 'react');
    expect(input).toHaveValue('react');

    await user.click(screen.getByRole('button', { name: /clear/i }));
    expect(input).toHaveValue('');
  });

  it('debounces search input', async () => {
    jest.useFakeTimers();
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    const onSearch = jest.fn();

    render(<SearchBar onSearch={onSearch} debounceMs={300} />);

    await user.type(screen.getByPlaceholderText(/search/i), 'react');

    expect(onSearch).not.toHaveBeenCalled();
    jest.advanceTimersByTime(300);
    expect(onSearch).toHaveBeenCalledWith('react');

    jest.useRealTimers();
  });
});
```

---

## Pattern 3: Async Operations

Test loading, success, and error states for components that fetch data.

```typescript
import { render, screen, waitFor } from '@/test-utils/render';
import { ProjectListContainer } from './ProjectListContainer';
import * as projectsService from '@/services/projects';

jest.mock('@/services/projects');

const mockFetchProjects = projectsService.fetchProjectsApi as jest.MockedFunction<
  typeof projectsService.fetchProjectsApi
>;

describe('ProjectListContainer', () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it('shows loading overlay while fetching', () => {
    mockFetchProjects.mockReturnValue(new Promise(() => {}));
    render(<ProjectListContainer />);
    // Mantine LoadingOverlay sets aria-busy
    expect(document.querySelector('[data-loading]')).toBeInTheDocument();
  });

  it('renders project list on success', async () => {
    mockFetchProjects.mockResolvedValue([
      { id: '1', name: 'Alpha', description: 'First', createdAt: '2024-01-01' },
      { id: '2', name: 'Beta', description: 'Second', createdAt: '2024-01-02' },
    ]);

    render(<ProjectListContainer />);

    await waitFor(() => {
      expect(screen.getByText('Alpha')).toBeInTheDocument();
      expect(screen.getByText('Beta')).toBeInTheDocument();
    });
  });

  it('shows error alert on failure', async () => {
    mockFetchProjects.mockRejectedValue(new Error('Server unavailable'));

    render(<ProjectListContainer />);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/server unavailable/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no projects exist', async () => {
    mockFetchProjects.mockResolvedValue([]);

    render(<ProjectListContainer />);

    await waitFor(() => {
      expect(screen.getByText(/no projects/i)).toBeInTheDocument();
    });
  });
});
```

---

## Pattern 4: Form Validation Testing

Test that form validation rules work correctly.

```typescript
import { render, screen, waitFor } from '@/test-utils/render';
import userEvent from '@testing-library/user-event';
import { CreateProjectForm } from './CreateProjectForm';
import * as projectsService from '@/services/projects';

jest.mock('@/services/projects');

describe('CreateProjectForm', () => {
  const user = userEvent.setup();

  it('shows error for name shorter than 2 characters', async () => {
    render(<CreateProjectForm />);

    await user.type(screen.getByLabelText(/name/i), 'A');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText(/name must be at least 2 characters/i)).toBeInTheDocument();
    });
  });

  it('shows error for empty required fields', async () => {
    render(<CreateProjectForm />);

    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText(/name must be at least/i)).toBeInTheDocument();
      expect(screen.getByText(/description is required/i)).toBeInTheDocument();
    });
  });

  it('clears errors when user corrects input', async () => {
    render(<CreateProjectForm />);

    // Trigger error
    await user.click(screen.getByRole('button', { name: /create/i }));
    await waitFor(() => {
      expect(screen.getByText(/name must be at least/i)).toBeInTheDocument();
    });

    // Fix the input
    await user.type(screen.getByLabelText(/name/i), 'Valid Name');
    await waitFor(() => {
      expect(screen.queryByText(/name must be at least/i)).not.toBeInTheDocument();
    });
  });

  it('resets form after successful submission', async () => {
    const mockCreate = projectsService.createProjectApi as jest.MockedFunction<
      typeof projectsService.createProjectApi
    >;
    mockCreate.mockResolvedValue({
      id: '1',
      name: 'Test',
      description: 'Desc',
      createdAt: '',
    });

    render(<CreateProjectForm />);

    await user.type(screen.getByLabelText(/name/i), 'Test Project');
    await user.type(screen.getByLabelText(/description/i), 'A description');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/name/i)).toHaveValue('');
      expect(screen.getByLabelText(/description/i)).toHaveValue('');
    });
  });
});
```

---

## Pattern 5: API Mocking with fetch

Mock the global `fetch` function for service-level tests.

```typescript
// Mock fetch globally
global.fetch = jest.fn();
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

function mockResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
  } as Response;
}

describe('request wrapper', () => {
  afterEach(() => mockFetch.mockReset());

  it('parses JSON response', async () => {
    mockFetch.mockResolvedValue(mockResponse({ id: '1', name: 'Test' }));
    const result = await request<{ id: string; name: string }>('/api/test');
    expect(result).toEqual({ id: '1', name: 'Test' });
  });

  it('throws on 4xx error', async () => {
    mockFetch.mockResolvedValue(mockResponse({ error: 'Not found' }, 404));
    await expect(request('/api/missing')).rejects.toThrow('Request failed: 404');
  });

  it('throws on 5xx error', async () => {
    mockFetch.mockResolvedValue(mockResponse({ error: 'Internal' }, 500));
    await expect(request('/api/broken')).rejects.toThrow('Request failed: 500');
  });

  it('sends correct headers', async () => {
    mockFetch.mockResolvedValue(mockResponse({}));
    await request('/api/test');
    expect(mockFetch).toHaveBeenCalledWith('/api/test', expect.objectContaining({
      headers: expect.objectContaining({
        'Content-Type': 'application/json',
      }),
    }));
  });
});
```

---

## Pattern 6: Accessibility Testing with jest-axe

```typescript
import { render } from '@/test-utils/render';
import { axe, toHaveNoViolations } from 'jest-axe';
import { LoginForm } from './LoginForm';

expect.extend(toHaveNoViolations);

describe('LoginForm accessibility', () => {
  it('has no a11y violations', async () => {
    const { container } = render(<LoginForm />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('has no a11y violations when showing errors', async () => {
    const { container } = render(<LoginForm />);
    // Trigger validation errors
    const submitButton = container.querySelector('button[type="submit"]');
    submitButton?.click();
    // Wait for error state
    await new Promise((resolve) => setTimeout(resolve, 0));
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

---

## Common Matchers Reference

```typescript
// DOM presence
expect(element).toBeInTheDocument();
expect(element).not.toBeInTheDocument();

// Text content
expect(element).toHaveTextContent('expected text');
expect(screen.getByText(/partial match/i)).toBeInTheDocument();

// Form values
expect(input).toHaveValue('expected value');
expect(checkbox).toBeChecked();
expect(select).toHaveValue('option-value');

// Attributes
expect(element).toHaveAttribute('href', '/expected');
expect(element).toHaveClass('active');
expect(button).toBeDisabled();
expect(input).toBeRequired();

// Visibility
expect(element).toBeVisible();

// Queries (by priority)
screen.getByRole('button', { name: /submit/i });  // Best - accessible
screen.getByLabelText(/email/i);                    // For form inputs
screen.getByPlaceholderText(/search/i);             // Fallback
screen.getByText(/welcome/i);                       // For display text
screen.getByTestId('custom-id');                     // Last resort
```
