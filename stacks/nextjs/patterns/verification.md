# Next.js Verification Pattern

## Overview

Next.js implementations are verified using MCP browser tools to render pages,
take screenshots, inspect DOM, check console errors, and validate accessibility.

## Prerequisites

- MCP browser server configured (Puppeteer or Playwright)
- Next.js dev server running on port 3000
- Components properly exported

## Verification Workflow

### 1. Start Dev Server

```bash
# Check if running
curl -s http://localhost:3000 || npm run dev &

# Wait for ready
until curl -s http://localhost:3000; do sleep 1; done
```

### 2. Navigate to Page

```javascript
browser_navigate({ url: "http://localhost:3000" })
```

### 3. Take Screenshot

```javascript
// Full page
browser_screenshot()

// Specific component
browser_screenshot({ selector: ".hero-section" })
```

### 4. Verify Component Renders

```javascript
browser_evaluate({
  script: `
    const el = document.querySelector('.hero-section');
    return el ? {
      found: true,
      visible: el.offsetParent !== null,
      rect: el.getBoundingClientRect()
    } : { found: false };
  `
})
```

### 5. Check Console Errors

```javascript
browser_evaluate({
  script: `window.__consoleErrors || []`
})
```

### 6. Test Responsiveness

```javascript
// Mobile
browser_evaluate({ script: `window.resizeTo(375, 812)` })
browser_screenshot()

// Desktop
browser_evaluate({ script: `window.resizeTo(1440, 900)` })
browser_screenshot()
```

## Component Verification

### Check Required Elements

```javascript
browser_evaluate({
  script: `
    const checks = {
      title: document.querySelector('h1'),
      cta: document.querySelector('.cta-button'),
      nav: document.querySelector('nav'),
      footer: document.querySelector('footer')
    };

    return Object.entries(checks).map(([name, el]) => ({
      name,
      found: !!el,
      text: el?.textContent?.trim().substring(0, 50)
    }));
  `
})
```

### Verify Interactive Elements

```javascript
// Click button
browser_click({ selector: ".cta-button" })
browser_screenshot()

// Fill form
browser_type({ selector: "input[name=email]", text: "test@example.com" })
browser_click({ selector: "button[type=submit]" })
browser_screenshot()

// Check result
browser_evaluate({
  script: `document.querySelector('.success-message')?.textContent`
})
```

### Check Loading States

```javascript
// Verify skeleton shows during load
browser_evaluate({
  script: `
    const skeletons = document.querySelectorAll('[data-loading], .skeleton');
    return skeletons.length;
  `
})
```

## Accessibility Verification

```javascript
browser_evaluate({
  script: `
    const issues = [];

    // Images need alt
    document.querySelectorAll('img:not([alt])').forEach(img =>
      issues.push({ rule: 'img-alt', element: img.src })
    );

    // Buttons need names
    document.querySelectorAll('button:empty:not([aria-label])').forEach(btn =>
      issues.push({ rule: 'button-name', element: btn.className })
    );

    // Form inputs need labels
    document.querySelectorAll('input:not([type=hidden])').forEach(input => {
      const id = input.id;
      const hasLabel = id && document.querySelector(\`label[for="\${id}"]\`);
      if (!hasLabel && !input.getAttribute('aria-label')) {
        issues.push({ rule: 'input-label', element: input.name || input.type });
      }
    });

    // Skip links
    const hasSkipLink = !!document.querySelector('[href="#main"], [href="#content"]');

    // Heading hierarchy
    const headings = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')];
    const levels = headings.map(h => parseInt(h.tagName[1]));
    let prevLevel = 0;
    levels.forEach((level, i) => {
      if (level > prevLevel + 1) {
        issues.push({
          rule: 'heading-order',
          element: \`h\${level} after h\${prevLevel}\`
        });
      }
      prevLevel = level;
    });

    return { issues, hasSkipLink, headingCount: headings.length };
  `
})
```

## Performance Checks

```javascript
browser_evaluate({
  script: `
    const perf = performance.getEntriesByType('navigation')[0];
    const lcp = performance.getEntriesByType('largest-contentful-paint')[0];

    return {
      domContentLoaded: perf.domContentLoadedEventEnd - perf.startTime,
      load: perf.loadEventEnd - perf.startTime,
      firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime,
      lcp: lcp?.startTime,
      resourceCount: performance.getEntriesByType('resource').length
    };
  `
})
```

## Auto-Fix Patterns

### Component Not Found

**Error:** `.hero-section not found`

**Check:**
1. Component exported from file
2. Component imported in page
3. Correct className applied

**Fix:**
```typescript
// components/index.ts
export { HeroSection } from './sections/HeroSection';

// app/page.tsx
import { HeroSection } from '@/components';

export default function Home() {
  return <HeroSection className="hero-section" />;
}
```

### Hydration Error

**Error:** `Hydration failed because the initial UI does not match`

**Fix:**
```typescript
// Use dynamic import with ssr: false
import dynamic from 'next/dynamic';

const ClientComponent = dynamic(() => import('./ClientComponent'), {
  ssr: false
});

// Or use useEffect for client-only code
const [mounted, setMounted] = useState(false);
useEffect(() => setMounted(true), []);
if (!mounted) return null;
```

### Console Error - Import

**Error:** `Cannot find module './Component'`

**Fix:**
- Check file exists
- Check file extension (.tsx)
- Check export syntax

### Accessibility Issue

**Error:** `Button missing accessible name`

**Fix:**
```typescript
// Add aria-label
<button aria-label="Close menu">
  <XIcon />
</button>

// Or add visible text
<button>
  <XIcon aria-hidden="true" />
  <span className="sr-only">Close menu</span>
</button>
```

## Verification Report Template

```markdown
# Next.js Verification Report

**Component:** HeroSection
**Page:** /
**Time:** TIMESTAMP

## Screenshots

| Viewport | Status |
|----------|--------|
| Desktop (1440px) | ✓ Captured |
| Tablet (768px) | ✓ Captured |
| Mobile (375px) | ✓ Captured |

## DOM Checks

| Element | Status | Details |
|---------|--------|---------|
| .hero-section | ✓ Found | Visible, 1200x600px |
| h1 | ✓ Found | "Welcome to..." |
| .cta-button | ✓ Found | 2 buttons |
| nav | ✓ Found | 5 links |

## Console

| Type | Count |
|------|-------|
| Errors | 0 |
| Warnings | 1 (React DevTools) |

## Accessibility

| Check | Status |
|-------|--------|
| Image alts | ✓ Pass |
| Button names | ✓ Pass |
| Form labels | ✓ Pass |
| Heading order | ✓ Pass |
| Skip link | ⚠ Missing |

## Performance

| Metric | Value | Status |
|--------|-------|--------|
| DOM Content Loaded | 450ms | ✓ Good |
| LCP | 1.2s | ✓ Good |
| Resources | 24 | ✓ OK |
```
