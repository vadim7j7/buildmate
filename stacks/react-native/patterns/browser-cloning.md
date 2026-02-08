# Browser Cloning Pattern

This pattern describes how to use the browser automation tools to analyze
and clone websites.

## Setup

### MCP Browser Configuration

Add one of these to your `.claude/settings.json`:

**Option 1: Puppeteer (Recommended)**
```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-puppeteer"]
    }
  }
}
```

**Option 2: Playwright**
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

After adding, restart Claude Code for the MCP server to connect.

## Available Tools

### Navigation

```
browser_navigate({ url: "https://example.com" })
```

Navigate to a URL and wait for the page to load.

### Screenshots

```
browser_screenshot()                    # Full page
browser_screenshot({ selector: ".hero" })  # Specific element
```

Capture screenshots for visual analysis.

### DOM Access

```
browser_get_html()                      # Full page HTML
browser_get_html({ selector: ".nav" })  # Specific element
```

Extract HTML structure for analysis.

### JavaScript Evaluation

```
browser_evaluate({
  script: `
    return {
      title: document.title,
      colors: getComputedStyle(document.body).backgroundColor
    };
  `
})
```

Run JavaScript to extract computed styles, data, etc.

### Interaction

```
browser_click({ selector: ".menu-button" })
browser_type({ selector: "input[name=email]", text: "test@example.com" })
browser_scroll({ direction: "down", amount: 500 })
```

Interact with the page to reveal hidden content or test states.

## Analysis Workflow

### 1. Initial Capture

```javascript
// Navigate and screenshot
browser_navigate({ url: "https://example.com" });
browser_screenshot();  // Analyze visually

// Get structure
browser_get_html();
```

### 2. Extract Design Tokens

```javascript
browser_evaluate({
  script: `
    const body = document.body;
    const styles = getComputedStyle(body);

    // Extract colors from all elements
    const colors = new Set();
    document.querySelectorAll('*').forEach(el => {
      const s = getComputedStyle(el);
      if (s.color) colors.add(s.color);
      if (s.backgroundColor !== 'rgba(0, 0, 0, 0)') {
        colors.add(s.backgroundColor);
      }
    });

    // Extract fonts
    const fonts = new Set();
    document.querySelectorAll('*').forEach(el => {
      fonts.add(getComputedStyle(el).fontFamily.split(',')[0].trim());
    });

    return {
      colors: [...colors],
      fonts: [...fonts],
      bodyFont: styles.fontFamily,
      bodyFontSize: styles.fontSize,
      bodyLineHeight: styles.lineHeight,
    };
  `
});
```

### 3. Analyze Components

```javascript
// Screenshot specific components
browser_screenshot({ selector: "header" });
browser_screenshot({ selector: ".hero" });
browser_screenshot({ selector: ".feature-card" });

// Extract component HTML
browser_get_html({ selector: ".feature-card" });
```

### 4. Test Responsive

```javascript
// Resize viewport for mobile
browser_evaluate({
  script: `window.resizeTo(375, 812);`
});
browser_screenshot();

// Back to desktop
browser_evaluate({
  script: `window.resizeTo(1440, 900);`
});
```

### 5. Capture Interactions

```javascript
// Hover state
browser_evaluate({
  script: `
    const btn = document.querySelector('.cta-button');
    btn.dispatchEvent(new MouseEvent('mouseenter'));
  `
});
browser_screenshot({ selector: ".cta-button" });
```

## Cloning Workflow

### 1. Analyze First

```
/analyze-site https://example.com
```

This produces `.agent-pipeline/site-analysis.md` with:
- Structure breakdown
- Design tokens
- Component inventory

### 2. Clone the Page

Choose your output format:

```
/clone-page https://example.com                     # Auto-detect from project
/clone-page https://example.com --format html       # Plain HTML + CSS
/clone-page https://example.com --format react      # React components
/clone-page https://example.com --format nextjs     # Next.js App Router
/clone-page https://example.com --format native     # React Native
/clone-page https://example.com --format vue        # Vue.js SFCs
/clone-page https://example.com --format svelte     # Svelte components
```

For React/Next.js, specify UI library:

```
/clone-page https://example.com --format nextjs --ui tailwind
/clone-page https://example.com --format nextjs --ui shadcn
/clone-page https://example.com --format react --ui chakra
```

This generates:
- Theme configuration (format-appropriate)
- Component files
- Page composition

### 3. Review and Refine

Check generated code:
- Verify component structure
- Adjust theme values
- Add missing interactions
- Replace placeholder content

## Output Formats

| Format | Output | Use Case |
|--------|--------|----------|
| `html` | HTML + CSS files | Static sites, prototypes |
| `react` | JSX + CSS Modules | React SPAs, Vite apps |
| `nextjs` | App Router components | Next.js projects |
| `native` | React Native + StyleSheet | Expo mobile apps |
| `vue` | Vue 3 SFCs | Vue.js projects |
| `svelte` | Svelte components | SvelteKit projects |

## UI Library Options (React/Next.js)

| Library | Description |
|---------|-------------|
| `plain` | CSS Modules (default for react) |
| `tailwind` | Tailwind CSS utilities |
| `mantine` | Mantine components (default for nextjs) |
| `shadcn` | shadcn/ui components |
| `chakra` | Chakra UI components |
| `mui` | Material UI components |

## Best Practices

### Do

- **Analyze before cloning** - understand the structure first
- **Start with landing pages** - they have clear sections
- **Use screenshots** - visual reference helps
- **Extract the design system** - colors, fonts, spacing
- **Build components bottom-up** - atoms → molecules → organisms

### Don't

- **Don't pixel-perfect copy** - focus on patterns
- **Don't include copyrighted assets** - use placeholders
- **Don't clone auth-gated content** - respect access controls
- **Don't skip responsive** - always check mobile
- **Don't forget accessibility** - preserve ARIA, semantics

## Common Patterns to Extract

### Hero Section
- Headline treatment (size, weight)
- CTA button styles
- Background (solid, gradient, image)
- Content alignment

### Navigation
- Logo placement
- Link styling
- Mobile menu pattern
- Sticky behavior

### Feature Grid
- Card layout (grid, flex)
- Icon style
- Heading hierarchy
- Spacing rhythm

### Testimonials
- Quote styling
- Avatar treatment
- Layout (carousel, grid)

### Footer
- Column organization
- Link grouping
- Social icons
- Legal text

## Troubleshooting

### MCP Not Connecting

1. Check settings.json syntax (valid JSON)
2. Restart Claude Code
3. Try `npx -y @anthropic-ai/mcp-server-puppeteer` manually

### JavaScript Sites Not Rendering

Use MCP browser instead of WebFetch. WebFetch only gets initial HTML,
not JavaScript-rendered content.

### Screenshots Not Working

Ensure the MCP server has screen access permissions on macOS.

### Slow Performance

- Use `--quick` flag for faster analysis
- Target specific sections instead of full page
- Close other browser instances
