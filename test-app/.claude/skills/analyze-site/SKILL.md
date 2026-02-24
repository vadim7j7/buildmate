---
name: analyze-site
description: Deep analysis of a website's structure, components, and design system
---

# /analyze-site

## What This Does

Performs deep analysis of a website to extract its structure, component patterns,
design system, and implementation details. Produces a comprehensive report that
can be used for learning, inspiration, or as input for `/clone-page`.

## Usage

```
/analyze-site https://example.com              # Full site analysis
/analyze-site https://example.com --quick      # Quick overview only
/analyze-site https://example.com --design     # Focus on design system
/analyze-site https://example.com --components # Focus on component patterns
/analyze-site https://example.com --compare https://other.com  # Compare two sites
```

## Requirements

**MCP Browser (recommended):**
Configure Puppeteer or Playwright MCP for screenshots and full DOM access.

**Without MCP Browser:**
Uses WebFetch for HTML content (limited for JavaScript-heavy sites).

## How It Works

1. **Navigate to the site** using MCP browser or WebFetch

2. **Capture visuals** (if browser MCP available):
   - Full page screenshot
   - Individual section screenshots
   - Responsive views (mobile, tablet, desktop)

3. **Extract structure:**
   - Page sections (header, hero, features, etc.)
   - Navigation hierarchy
   - Content organization

4. **Analyze design system:**
   - Color palette
   - Typography (fonts, sizes, weights)
   - Spacing patterns
   - Border radii and shadows

5. **Identify components:**
   - Buttons, cards, forms, modals
   - Reusable patterns
   - Component variants

6. **Document interactions:**
   - Hover states
   - Animations
   - Transitions

7. **Check responsiveness:**
   - Breakpoints
   - Mobile adaptations
   - Layout changes

8. **Write report** to `.agent-pipeline/site-analysis.md`

## Example Output

```markdown
# Site Analysis: https://vercel.com

**Analyzed:** 2026-02-08 14:30
**URL:** https://vercel.com

## Overview

Vercel's homepage is a modern, dark-themed landing page focused on developer
experience. Clean typography, generous whitespace, and subtle animations
create a premium feel.

## Structure

| Section | Description |
|---------|-------------|
| Header | Sticky nav with logo, product links, CTAs |
| Hero | Bold headline with animated gradient, demo terminal |
| Features | Grid of feature cards with icons |
| Integrations | Logo cloud of supported frameworks |
| Testimonials | Customer quotes in cards |
| Pricing | Three-tier pricing table |
| CTA | Final call to action |
| Footer | Multi-column links, social, legal |

## Design System

### Colors

| Name | Hex | Usage |
|------|-----|-------|
| Background | #000000 | Page background |
| Foreground | #FFFFFF | Primary text |
| Muted | #888888 | Secondary text |
| Accent | #0070F3 | Links, buttons |
| Gradient Start | #FF0080 | Hero gradient |
| Gradient End | #7928CA | Hero gradient |

### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| H1 | Inter | 64px | 700 |
| H2 | Inter | 48px | 600 |
| H3 | Inter | 24px | 600 |
| Body | Inter | 16px | 400 |
| Small | Inter | 14px | 400 |

### Spacing

- Base unit: 8px
- Section padding: 80px vertical
- Component gap: 24px
- Card padding: 24px

## Components Identified

### 1. NavBar
- Logo left, links center, CTAs right
- Transparent → solid on scroll
- Hamburger menu on mobile

### 2. HeroSection
- Massive headline (64px)
- Animated gradient background
- Terminal demo component
- Two CTA buttons (primary/secondary)

### 3. FeatureCard
- Icon (40x40, accent color)
- Title (H3)
- Description (body text, muted)
- Optional link

### 4. PricingCard
- Header with plan name
- Price with period
- Feature list with checkmarks
- CTA button
- "Popular" badge variant

## Interactions

| Element | Trigger | Effect |
|---------|---------|--------|
| Nav links | Hover | Underline animation |
| Buttons | Hover | Scale 1.02, lighten |
| Cards | Hover | Subtle lift (shadow) |
| Hero gradient | Load | Continuous animation |

## Responsive Behavior

| Breakpoint | Changes |
|------------|---------|
| < 768px | Hamburger nav, single column, smaller text |
| < 1024px | Two-column grids become single |
| > 1280px | Max-width container (1200px) |

## Accessibility

- Good contrast ratios (dark bg, white text)
- Semantic HTML structure
- Skip to content link
- ARIA labels on interactive elements

## Performance Notes

- Lazy loaded images
- Font loading: Inter via next/font
- Minimal JavaScript for static content
- Animations use CSS transforms (GPU accelerated)

## Recreation Recommendations

1. Use CSS custom properties for the color palette
2. Inter font from Google Fonts or next/font
3. CSS Grid for feature sections
4. Framer Motion for animations (optional)
5. Dark mode as default (no toggle needed)
```

## Options

| Option | Description |
|--------|-------------|
| `--quick` | Quick overview (structure + colors only) |
| `--design` | Focus on design system extraction |
| `--components` | Focus on component pattern identification |
| `--responsive` | Include responsive behavior analysis |
| `--accessibility` | Include accessibility audit |
| `--compare <url>` | Compare with another site |
| `--output <file>` | Custom output file location |

## Use Cases

1. **Before cloning** - Understand what you're working with
2. **Learning** - Study how top sites are built
3. **Competitive analysis** - Compare design patterns
4. **Design system extraction** - Pull colors/fonts for your project
5. **Inspiration** - Document patterns you want to adopt

## Tips

- **Analyze multiple pages** for full component coverage
- **Check mobile view** for responsive patterns
- **Look at interaction states** by scrolling, hovering
- **Compare similar sites** to identify common patterns
- **Save analyses** for future reference
