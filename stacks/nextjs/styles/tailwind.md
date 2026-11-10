# Tailwind CSS Style Guide (v4)

## Overview

Use Tailwind CSS v4 utility classes for all styling. v4 is **CSS-first**: the theme
lives in CSS (`@theme`), not in `tailwind.config.js`. Don't create a JS config in a
new project; an existing v3 config can be loaded with `@config "../../tailwind.config.js";`
until it is migrated (`npx @tailwindcss/upgrade`).

## Setup (Next.js)

```bash
npm install tailwindcss @tailwindcss/postcss
```

```js
// postcss.config.mjs
export default {
  plugins: { '@tailwindcss/postcss': {} },
};
```

```css
/* src/app/globals.css (imported once, in the root layout) */
@import "tailwindcss";

/* Design tokens: each variable becomes utilities (bg-primary, text-primary, font-sans...) */
@theme {
  --color-primary: oklch(0.55 0.2 260);
  --color-primary-foreground: oklch(0.98 0 0);
  --color-danger: oklch(0.58 0.22 27);
  --font-sans: var(--font-inter), ui-sans-serif, system-ui, sans-serif;
  --breakpoint-3xl: 120rem;
}

/* Class-based dark mode (default is prefers-color-scheme) */
@custom-variant dark (&:where(.dark, .dark *));
```

- Source files are detected automatically (no `content` array). Add `@source "../../packages/ui";`
  only for files outside the project root or ignored by git.
- Plugins load in CSS: `@plugin "@tailwindcss/typography";`.
- In a CSS module that uses `@apply`, add `@reference "../app/globals.css";` so the
  theme is known.

## Class Organization

Let `prettier-plugin-tailwindcss` sort classes (add it to the Prettier plugins). Don't
hand-sort or argue about order in review.

## Responsive Design

Mobile-first with breakpoint prefixes; container queries are built in:

```tsx
<div className="flex flex-col gap-4 md:flex-row">
<div className="@container">
  <div className="grid grid-cols-1 @md:grid-cols-2">
```

## Color Usage

Use the semantic tokens from `@theme`, not raw palette colors:

```tsx
// Good
<button className="bg-primary text-primary-foreground hover:bg-primary/90">

// Avoid outside the theme
<button className="bg-blue-600 text-white">
```

Opacity uses the slash modifier (`bg-black/50`); `bg-opacity-*` / `text-opacity-*`
no longer exist.

## v3 → v4 Renames (don't write the old names)

| v3 | v4 |
|----|----|
| `shadow-sm` / `shadow` | `shadow-xs` / `shadow-sm` |
| `rounded-sm` / `rounded` | `rounded-xs` / `rounded-sm` |
| `blur-sm` / `blur` | `blur-xs` / `blur-sm` |
| `outline-none` | `outline-hidden` (`outline-none` now sets `outline-style: none`) |
| `ring` (3px) | `ring-3` (`ring` is 1px now) |
| `flex-shrink-0` / `flex-grow` | `shrink-0` / `grow` |
| `bg-gradient-to-r` | `bg-linear-to-r` |

Borders and rings default to `currentColor`: always give a color (`border border-gray-200`).

## Composing Classes

Use a `cn()` helper (clsx + tailwind-merge v3, which understands v4 classes) for
conditional classes and overrides:

```tsx
// src/lib/cn.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

```tsx
// src/components/ui/Button.tsx
import { cn } from '@/lib/cn';

type ButtonProps = React.ComponentProps<'button'> & {
  variant?: 'primary' | 'secondary' | 'danger';
};

const variants = {
  primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
  secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200',
  danger: 'bg-danger text-white hover:bg-danger/90',
} as const;

export function Button({ variant = 'primary', className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'rounded-md px-4 py-2 font-medium focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-50',
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
```

## Dark Mode

```tsx
<div className="bg-white text-gray-900 dark:bg-gray-900 dark:text-white">
```

Prefer tokens that switch in CSS (override the `--color-*` variables under `.dark`)
over sprinkling `dark:` on every element.

## Avoid

- A new `tailwind.config.js` (use `@theme`)
- `@tailwind base; @tailwind components; @tailwind utilities;` (v3 syntax; use `@import "tailwindcss"`)
- Building class names dynamically (`` `bg-${color}-500` ``): the scanner can't see them; map to full class strings
- Inline styles (`style={{}}`) for anything a utility covers
- Magic values (`w-[437px]`) when a theme value exists
