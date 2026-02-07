---
name: clone-page
description: Clone a webpage into your project using the project's UI library
---

# /clone-page

## What This Does

Analyzes a webpage and generates equivalent components in your project's
stack and UI library. Creates production-ready, accessible code that matches
the visual design.

## Usage

```
/clone-page https://example.com              # Clone the full page
/clone-page https://example.com/pricing      # Clone a specific page
/clone-page https://example.com --section hero  # Clone only the hero section
/clone-page https://example.com --components    # Extract reusable components only
```

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
   - Create atomic components (buttons, inputs, cards)
   - Create section components (hero, features, footer)
   - Use the project's UI library (Mantine, Tailwind, shadcn, etc.)
   - Follow project conventions and file structure

4. **Compose the page.** Create the full page component that:
   - Imports and arranges all sections
   - Applies the theme
   - Handles responsive behavior

5. **Report results.** Write summary to `.agent-pipeline/clone-report.md`

## Example Workflow

```
User: /clone-page https://linear.app

Agent: I'll analyze and clone the Linear homepage.

[Delegates to site-analyzer]
- Navigating to https://linear.app
- Taking screenshot
- Extracting structure: Header, Hero, Features, Testimonials, CTA, Footer
- Extracting design tokens: colors (#5E6AD2 primary), Inter font, etc.

[Delegates to ui-cloner]
- Generating theme.ts with Linear's design tokens
- Creating components:
  - Header.tsx (sticky nav with logo, links, CTAs)
  - HeroSection.tsx (headline, subheading, demo video)
  - FeaturesGrid.tsx (feature cards with icons)
  - TestimonialsSection.tsx (customer quotes)
  - CTASection.tsx (final call to action)
  - Footer.tsx (links, social, legal)

[Report]
Created 8 components in src/components/
Updated theme in src/styles/theme.ts
Page ready at src/app/page.tsx
```

## Output Files

```
src/
├── styles/
│   └── theme.ts              # Design tokens from source
├── components/
│   ├── layout/
│   │   ├── Header.tsx
│   │   └── Footer.tsx
│   └── sections/
│       ├── HeroSection.tsx
│       ├── FeaturesSection.tsx
│       └── CTASection.tsx
└── app/
    └── cloned-page/
        └── page.tsx          # Composed page
```

## Options

| Option | Description |
|--------|-------------|
| `--section <name>` | Clone only a specific section (hero, features, footer) |
| `--components` | Extract reusable components without composing page |
| `--theme-only` | Extract only the design tokens/theme |
| `--no-theme` | Use existing theme, don't extract new one |
| `--output <dir>` | Custom output directory for components |

## Tips

- **Start with simpler pages** - Landing pages work best
- **Review the analysis first** - Run `/analyze-site` before cloning
- **Iterate** - Clone, review, adjust, repeat
- **Check existing components** - Avoid duplicating what you have
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
