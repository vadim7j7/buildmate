# Playwright E2E Testing Patterns

## Setup

### Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## Pattern 1: Page Navigation

Test that pages load correctly and navigation works.

```typescript
import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('homepage loads and displays title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/my app/i);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('navigates to projects page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: /projects/i }).click();
    await expect(page).toHaveURL('/projects');
    await expect(page.getByRole('heading', { name: /projects/i })).toBeVisible();
  });

  test('navigates to project detail page', async ({ page }) => {
    await page.goto('/projects');
    await page.getByRole('link', { name: /my project/i }).first().click();
    await expect(page).toHaveURL(/\/projects\/[\w-]+/);
  });

  test('shows 404 page for invalid routes', async ({ page }) => {
    await page.goto('/this-does-not-exist');
    await expect(page.getByText(/not found/i)).toBeVisible();
  });
});
```

---

## Pattern 2: Form Filling and Submission

Test form interactions including validation and submission.

```typescript
import { test, expect } from '@playwright/test';

test.describe('Create Project Form', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects/new');
  });

  test('submits form with valid data', async ({ page }) => {
    await page.getByLabel(/name/i).fill('New Project');
    await page.getByLabel(/description/i).fill('A test project');
    await page.getByRole('button', { name: /create/i }).click();

    // Expect success notification
    await expect(page.getByText(/project created/i)).toBeVisible();

    // Expect redirect to project list or detail page
    await expect(page).toHaveURL(/\/projects/);
  });

  test('shows validation errors for empty fields', async ({ page }) => {
    await page.getByRole('button', { name: /create/i }).click();

    await expect(page.getByText(/name must be at least/i)).toBeVisible();
    await expect(page.getByText(/description is required/i)).toBeVisible();
  });

  test('shows server error on submission failure', async ({ page }) => {
    // Mock API to return error
    await page.route('/api/projects', (route) => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Internal error' }) });
    });

    await page.getByLabel(/name/i).fill('New Project');
    await page.getByLabel(/description/i).fill('A test project');
    await page.getByRole('button', { name: /create/i }).click();

    await expect(page.getByText(/failed to create/i)).toBeVisible();
  });

  test('clears form after cancel', async ({ page }) => {
    await page.getByLabel(/name/i).fill('Temporary');
    await page.getByRole('button', { name: /cancel/i }).click();

    await expect(page.getByLabel(/name/i)).toHaveValue('');
  });
});
```

---

## Pattern 3: Assertions and Expectations

Common assertion patterns for Playwright tests.

```typescript
import { test, expect } from '@playwright/test';

test.describe('Assertions', () => {
  test('element visibility', async ({ page }) => {
    await page.goto('/');

    // Visible
    await expect(page.getByRole('heading')).toBeVisible();

    // Hidden
    await expect(page.getByTestId('modal')).toBeHidden();

    // Enabled/Disabled
    await expect(page.getByRole('button', { name: /submit/i })).toBeEnabled();
    await expect(page.getByRole('button', { name: /loading/i })).toBeDisabled();
  });

  test('text content', async ({ page }) => {
    await page.goto('/projects');

    // Exact text
    await expect(page.getByRole('heading')).toHaveText('Projects');

    // Contains text
    await expect(page.locator('.description')).toContainText('overview');

    // Count elements
    await expect(page.getByRole('listitem')).toHaveCount(5);
  });

  test('URL and title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL('http://localhost:3000/');
    await expect(page).toHaveTitle(/home/i);
  });

  test('attribute values', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('link', { name: /docs/i })).toHaveAttribute('href', '/docs');
  });
});
```

---

## Pattern 4: Authentication Flow Testing

Test login, logout, and protected routes.

```typescript
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('login with valid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel(/email/i).fill('user@example.com');
    await page.getByLabel(/password/i).fill('securepassword123');
    await page.getByRole('button', { name: /sign in/i }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText(/welcome/i)).toBeVisible();
  });

  test('login with invalid credentials shows error', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel(/email/i).fill('wrong@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page.getByText(/invalid credentials/i)).toBeVisible();
    await expect(page).toHaveURL('/login');
  });

  test('logout clears session', async ({ page }) => {
    // Assume logged in (via storage state or API setup)
    await page.goto('/dashboard');
    await page.getByRole('button', { name: /logout/i }).click();

    await expect(page).toHaveURL('/login');
  });

  test('protected route redirects to login when not authenticated', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/login');
  });
});

// Reusable auth setup
test.describe('Authenticated routes', () => {
  test.use({
    storageState: 'e2e/.auth/user.json',
  });

  test('dashboard loads for authenticated user', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });
});
```

### Auth Setup Script

```typescript
// e2e/global-setup.ts
import { chromium, type FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto('http://localhost:3000/login');
  await page.getByLabel(/email/i).fill('test@example.com');
  await page.getByLabel(/password/i).fill('testpassword');
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL('/dashboard');

  await page.context().storageState({ path: 'e2e/.auth/user.json' });
  await browser.close();
}

export default globalSetup;
```

---

## Pattern 5: API Mocking and Interception

Mock API responses for deterministic E2E tests.

```typescript
import { test, expect } from '@playwright/test';

test.describe('API Mocking', () => {
  test('displays mocked project data', async ({ page }) => {
    await page.route('/api/projects', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: '1', name: 'Mocked Project', description: 'From mock' },
        ]),
      });
    });

    await page.goto('/projects');
    await expect(page.getByText('Mocked Project')).toBeVisible();
  });

  test('handles API timeout gracefully', async ({ page }) => {
    await page.route('/api/projects', (route) => {
      // Simulate timeout by not responding
      route.abort('timedout');
    });

    await page.goto('/projects');
    await expect(page.getByText(/failed to load/i)).toBeVisible();
  });
});
```

---

## Pattern 6: Visual Regression Basics

Capture screenshots for visual comparison.

```typescript
import { test, expect } from '@playwright/test';

test.describe('Visual regression', () => {
  test('homepage matches snapshot', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveScreenshot('homepage.png', {
      fullPage: true,
      maxDiffPixelRatio: 0.01,
    });
  });

  test('project card matches snapshot', async ({ page }) => {
    await page.goto('/projects');
    const card = page.getByTestId('project-card').first();
    await expect(card).toHaveScreenshot('project-card.png');
  });

  test('dark mode matches snapshot', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /toggle theme/i }).click();
    await expect(page).toHaveScreenshot('homepage-dark.png', { fullPage: true });
  });
});
```

---

## Best Practices

1. **Use role-based selectors** (`getByRole`, `getByLabel`) over test IDs
2. **Avoid hard waits** (`page.waitForTimeout`) -- use assertions that auto-wait
3. **Isolate tests** -- each test should not depend on state from another
4. **Mock external APIs** for deterministic results
5. **Use `test.describe`** to group related tests
6. **Use `test.beforeEach`** for common setup (navigation, auth)
7. **Capture screenshots on failure** (configured in playwright.config.ts)
8. **Run in CI** with retries to handle flakiness
