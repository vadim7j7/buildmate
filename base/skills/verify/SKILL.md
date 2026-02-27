---
name: verify
description: Verify implementation by testing it - HTTP requests for APIs, browser testing for UI
---

# /verify

## What This Does

Automatically tests your implementation by actually running it:
- **Backend**: Makes HTTP requests, validates responses
- **Frontend**: Uses MCP browser to render, screenshot, check DOM
- **Mobile**: Launches in simulator/Expo, captures screens

## Usage

```bash
/verify                              # Verify last change (auto-detect)
/verify --endpoint POST /api/users   # Verify specific endpoint
/verify --component HeroSection      # Verify specific component
/verify --page /pricing              # Verify full page
/verify --all                        # Verify all recent changes
```

## How It Works

### 1. Detect Stack

Reads project configuration to determine verification strategy:
- Rails/FastAPI/Django/Flask/Express/Sinatra → HTTP testing
- Gin/Fiber/Chi → HTTP testing (Go)
- Phoenix → HTTP testing (Elixir)
- Next.js/Nuxt → Browser testing via MCP
- React Native → Expo/Simulator testing

### 2. Ensure Dev Server Running

```bash
# Check if server is running
curl -s http://localhost:3000/health || npm run dev &
```

### 3. Run Stack-Specific Verification

**Backend (Rails/FastAPI):**
```bash
# Test endpoint
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test"}' \
  -w "\n%{http_code}"

# Verify response
- Status code matches expected (200, 201, etc.)
- Response body has expected structure
- No error messages
```

**Frontend (Next.js):**
```javascript
// Navigate to page
browser_navigate({ url: "http://localhost:3000/pricing" })

// Take screenshot for visual verification
browser_screenshot()

// Check component renders
browser_evaluate({
  script: `document.querySelector('.hero-section') !== null`
})

// Check for console errors
browser_evaluate({
  script: `window.__consoleErrors || []`
})

// Check accessibility basics
browser_evaluate({
  script: `
    const issues = [];
    document.querySelectorAll('img:not([alt])').forEach(() =>
      issues.push('Image missing alt text')
    );
    document.querySelectorAll('button:not([aria-label]):empty').forEach(() =>
      issues.push('Button missing label')
    );
    return issues;
  `
})
```

**Mobile (React Native):**
```bash
# Check Expo dev server
curl http://localhost:8081/status

# For component testing, use Jest
npm test -- --testPathPattern="HeroSection"
```

### 4. Analyze Results

| Result | Action |
|--------|--------|
| Pass | Report success, continue |
| Fail | Analyze error, attempt fix, retry |
| Error | Report issue, ask for help |

### 5. Fix Loop (if enabled)

```
verify → fail → analyze → fix → verify → pass
         ↑__________________________|
              (max 3 retries)
```

## Verification Levels

| Level | Flag | What It Tests |
|-------|------|---------------|
| Unit | `--unit` | Single component/endpoint |
| Integration | `--integration` | Multiple components together |
| E2E | `--e2e` | Full user flow |
| All | `--all` | Everything changed |

## Stack-Specific Options

### Backend (Rails/FastAPI/Django/Flask/Express/Sinatra/Gin/Fiber/Chi/Phoenix)

```bash
/verify --endpoint GET /api/users           # Test specific endpoint
/verify --endpoint POST /api/users --data '{"name": "test"}'
/verify --model User                        # Test model validations
/verify --auth                              # Test with authentication
```

### Frontend (Next.js/Nuxt)

```bash
/verify --component Button                  # Test component renders
/verify --page /dashboard                   # Test full page
/verify --responsive                        # Test mobile/tablet/desktop
/verify --a11y                              # Accessibility audit
/verify --performance                       # Core Web Vitals
```

### Mobile (React Native)

```bash
/verify --screen HomeScreen                 # Test screen renders
/verify --platform ios                      # iOS specific
/verify --platform android                  # Android specific
```

## Configuration

In your project's `.claude/settings.json`:

```json
{
  "verification": {
    "enabled": true,
    "autoVerify": true,
    "maxRetries": 3,
    "devServer": {
      "command": "npm run dev",
      "port": 3000,
      "healthCheck": "/api/health",
      "startupTimeout": 30000
    },
    "browser": {
      "headless": true,
      "viewport": { "width": 1280, "height": 720 }
    }
  }
}
```

To disable during bootstrap:

```bash
buildmate nextjs /path/to/app --no-verify
```

## Example Workflows

### After Creating an API Endpoint

```
Developer: Creates POST /api/users endpoint

Agent: I'll verify this endpoint works.

[Starting verification]
- Dev server running on :3000 ✓
- POST /api/users with test data...
- Response: 201 Created ✓
- Body: { "id": 1, "email": "test@example.com" } ✓
- Schema validation: passed ✓

Verification passed! Endpoint working correctly.
```

### After Creating a Component

```
Developer: Creates PricingCard component

Agent: I'll verify this component renders correctly.

[Starting verification]
- Dev server running on :3000 ✓
- Navigating to /pricing...
- Screenshot captured ✓
- Component .pricing-card found ✓
- No console errors ✓
- Accessibility check: 1 warning (contrast ratio)

Verification passed with warnings.
Consider: Increase text contrast on muted price text.
```

### Verification Fails → Auto-Fix

```
Agent: Creating HeroSection component...

[Starting verification]
- Navigating to /...
- Component .hero-section NOT FOUND ✗

[Analyzing failure]
- Component not exported from index
- Adding export...

[Retry verification]
- Component .hero-section found ✓
- Screenshot captured ✓

Verification passed after 1 fix.
```

## Verification Report

After verification, a report is written to `.agent-pipeline/verification-report.md`:

```markdown
# Verification Report

**Time:** 2024-02-08 14:30:00
**Stack:** nextjs
**Target:** PricingCard component

## Results

| Check | Status | Details |
|-------|--------|---------|
| Renders | ✓ Pass | Component found in DOM |
| No Errors | ✓ Pass | Console clean |
| Responsive | ✓ Pass | Tested 3 viewports |
| A11y | ⚠ Warning | 1 contrast issue |

## Screenshots

- Desktop: `.agent-pipeline/screenshots/pricing-desktop.png`
- Mobile: `.agent-pipeline/screenshots/pricing-mobile.png`

## Fixes Applied

1. Added missing export to components/index.ts

## Recommendations

1. Improve contrast ratio on `.price-muted` class
```

## Integration with Developer Agents

Developer agents automatically call `/verify` after implementation:

```markdown
## Implementation Workflow

1. Implement the feature
2. Run quality gates (lint, typecheck)
3. **Call /verify to test implementation**
4. If verify fails:
   - Analyze the error
   - Apply fix
   - Retry verification (max 3 times)
5. If verify passes:
   - Continue to next task
6. If still failing after retries:
   - Report issue to user
   - Ask for guidance
```

## Disabling Verification

```bash
# Disable for single command
/verify --skip

# Disable in settings
{
  "verification": {
    "enabled": false
  }
}

# Disable during bootstrap
buildmate nextjs /path --no-auto-verify
```
