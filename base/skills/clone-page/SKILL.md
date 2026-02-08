---
name: clone-page
description: Clone a webpage into any format - HTML, React, Next.js, React Native, Vue, or Svelte
---

# /clone-page

## What This Does

Analyzes a webpage and generates equivalent code in your chosen format. Creates
production-ready, accessible code that matches the visual design.

## Usage

```
/clone-page https://example.com                     # Auto-detect from project stack
/clone-page https://example.com --format html       # Plain HTML + CSS
/clone-page https://example.com --format react      # React components
/clone-page https://example.com --format nextjs     # Next.js App Router
/clone-page https://example.com --format native     # React Native
/clone-page https://example.com --format vue        # Vue.js SFCs
/clone-page https://example.com --format svelte     # Svelte components
```

## Output Formats

| Format | Output | Use Case |
|--------|--------|----------|
| `html` | HTML + CSS files | Static sites, email templates, prototypes |
| `react` | JSX + CSS Modules/styled-components | React SPAs, Vite apps |
| `nextjs` | Next.js App Router components | Next.js projects |
| `native` | React Native + StyleSheet | Mobile apps with Expo |
| `vue` | Vue 3 SFCs with `<script setup>` | Vue.js projects |
| `svelte` | Svelte components | SvelteKit projects |
| `auto` | Detect from project | Default behavior |

## Requirements

**MCP Browser (recommended):**
For best results, configure the Puppeteer or Playwright MCP server in your
settings.json. This enables screenshots and full DOM access.

**Without MCP Browser:**
Falls back to WebFetch which provides HTML content but no screenshots
or JavaScript-rendered content.

## How It Works

1. **Analyze the page.** Delegate to the site-analyzer agent to:
   - Fetch the page content (via MCP browser or WebFetch)
   - Take screenshots if browser MCP is available
   - Extract structure, components, and design tokens
   - Write analysis to `.agent-pipeline/site-analysis.md`

2. **Generate theme.** Extract design tokens and create/update theme:
   - Colors (primary, secondary, accent, etc.)
   - Typography (fonts, sizes, weights)
   - Spacing scale
   - Border radii and shadows

3. **Generate components.** Delegate to the ui-cloner agent to:
   - Create components in the specified format
   - Use appropriate styling approach for the format
   - Follow conventions for each framework/library

4. **Compose the page.** Create the full page component that:
   - Imports and arranges all sections
   - Applies the theme
   - Handles responsive behavior

5. **Report results.** Write summary to `.agent-pipeline/clone-report.md`

## Format-Specific Output

### HTML (`--format html`)

```
output/
├── index.html          # Semantic HTML structure
├── styles/
│   ├── reset.css       # CSS reset
│   ├── variables.css   # CSS custom properties (theme)
│   └── main.css        # Component styles
└── assets/
    └── (placeholder images)
```

### React (`--format react`)

```
src/
├── components/
│   ├── ui/             # Atomic components
│   ├── sections/       # Page sections
│   └── layout/         # Layout components
├── styles/
│   ├── theme.ts        # Design tokens
│   └── global.css      # Global styles
└── App.tsx             # Composed page
```

### Next.js (`--format nextjs`)

```
src/
├── components/
│   ├── ui/
│   ├── sections/
│   └── layout/
├── styles/
│   └── theme.ts
└── app/
    └── page.tsx        # App Router page
```

### React Native (`--format native`)

```
src/
├── components/
│   ├── ui/
│   ├── sections/
│   └── layout/
├── theme/
│   └── index.ts        # Design tokens
└── screens/
    └── ClonedScreen.tsx
```

### Vue (`--format vue`)

```
src/
├── components/
│   ├── ui/             # Base components
│   └── sections/       # Section components
├── styles/
│   └── variables.css   # CSS custom properties
└── views/
    └── ClonedPage.vue  # Page component
```

### Svelte (`--format svelte`)

```
src/
├── lib/
│   ├── components/
│   │   ├── ui/
│   │   └── sections/
│   └── styles/
│       └── theme.ts
└── routes/
    └── +page.svelte    # SvelteKit page
```

## UI Library Support

When using `--format react` or `--format nextjs`, you can specify a UI library:

```
/clone-page https://example.com --format nextjs --ui mantine
/clone-page https://example.com --format nextjs --ui tailwind
/clone-page https://example.com --format nextjs --ui shadcn
/clone-page https://example.com --format react --ui chakra
/clone-page https://example.com --format react --ui mui
```

| UI Library | Description |
|------------|-------------|
| `plain` | Plain CSS/CSS Modules (default for react) |
| `tailwind` | Tailwind CSS utility classes |
| `mantine` | Mantine UI components (default for nextjs) |
| `shadcn` | shadcn/ui components |
| `chakra` | Chakra UI components |
| `mui` | Material UI components |

## Options

| Option | Description |
|--------|-------------|
| `--format <fmt>` | Output format: html, react, nextjs, native, vue, svelte, auto |
| `--ui <library>` | UI library for React/Next.js (see above) |
| `--section <name>` | Clone only a specific section (hero, features, footer) |
| `--components` | Extract reusable components without composing page |
| `--theme-only` | Extract only the design tokens/theme |
| `--no-theme` | Use existing theme, don't extract new one |
| `--output <dir>` | Custom output directory for components |

## Example Workflows

### Clone as plain HTML

```
User: /clone-page https://stripe.com/payments --format html

Agent: I'll clone the Stripe Payments page as static HTML.

[Analysis]
- Structure: Hero, Features Grid, Pricing Table, FAQ, Footer
- Colors: #635BFF (primary), #0A2540 (dark), #F6F9FC (light)
- Font: Inter, system-ui

[Generation]
Created:
- index.html (semantic HTML5)
- styles/variables.css (CSS custom properties)
- styles/main.css (component styles)

Open index.html in your browser to preview.
```

### Clone for React SPA

```
User: /clone-page https://linear.app --format react --ui tailwind

Agent: I'll clone Linear's homepage as React + Tailwind components.

[Generation]
- src/components/ui/Button.tsx
- src/components/sections/HeroSection.tsx
- src/components/sections/FeaturesSection.tsx
- src/styles/theme.ts
- src/App.tsx
```

### Clone for mobile

```
User: /clone-page https://example.com --format native

Agent: I'll convert this design to React Native components.

[Generation]
- src/components/ui/Button.tsx
- src/components/sections/HeroSection.tsx
- src/theme/index.ts
- src/screens/ClonedScreen.tsx
```

## Tips

- **Start with simpler pages** - Landing pages work best
- **Review the analysis first** - Run `/analyze-site` before cloning
- **Iterate** - Clone, review, adjust, repeat
- **Match your stack** - Use `auto` format when in a project
- **Customize after** - Clone gets you 80%, you refine the rest

## Limitations

- Cannot clone authentication-gated pages
- JavaScript-heavy SPAs need MCP browser for full analysis
- Some animations/interactions need manual recreation
- Assets (images, fonts) need separate handling

## Ethical Use

This tool is for **learning and inspiration**. Do not:
- Directly copy proprietary designs without permission
- Clone sites to deceive users (phishing)
- Violate terms of service or copyright

Use cloned code as a **starting point** and customize to make it your own.
