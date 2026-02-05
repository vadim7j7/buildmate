# Tailwind CSS Style Guide

## Overview

Use Tailwind CSS utility classes for all styling. Follow the project's design system.

## Class Organization

Order classes consistently:

1. Layout (display, position, grid, flex)
2. Spacing (margin, padding)
3. Size (width, height)
4. Typography (font, text)
5. Colors (bg, text, border)
6. Effects (shadow, opacity)
7. States (hover, focus)

```tsx
// Good: organized class order
<div className="flex items-center gap-4 p-4 w-full text-lg text-gray-900 bg-white rounded-lg shadow-md hover:shadow-lg">

// Bad: random order
<div className="shadow-md text-lg p-4 flex hover:shadow-lg bg-white gap-4 items-center">
```

## Responsive Design

Mobile-first approach with breakpoint prefixes:

```tsx
// Mobile: stack, Tablet+: row
<div className="flex flex-col md:flex-row gap-4">

// Full width on mobile, half on desktop
<div className="w-full lg:w-1/2">
```

## Component Patterns

### Button

```tsx
<button className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed">
  Click me
</button>
```

### Card

```tsx
<div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
  <h3 className="text-lg font-semibold text-gray-900">Title</h3>
  <p className="mt-2 text-gray-600">Content</p>
</div>
```

### Form Input

```tsx
<input
  type="text"
  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
/>
```

## Color Usage

Use semantic color names from your theme:

```tsx
// Good: semantic colors
className="text-primary bg-secondary border-error"

// Avoid: hardcoded colors unless in theme
className="text-blue-600 bg-gray-100 border-red-500"
```

## Spacing Scale

Use consistent spacing values:

| Class | Size |
|-------|------|
| `p-1`, `m-1` | 4px |
| `p-2`, `m-2` | 8px |
| `p-4`, `m-4` | 16px |
| `p-6`, `m-6` | 24px |
| `p-8`, `m-8` | 32px |

## Dark Mode

Support dark mode with the `dark:` prefix:

```tsx
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
```

## Custom Components

Extract repeated patterns into components:

```tsx
// components/ui/button.tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  children: React.ReactNode;
}

const variants = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700',
  secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300',
  danger: 'bg-red-600 text-white hover:bg-red-700',
};

export function Button({ variant = 'primary', children }: ButtonProps) {
  return (
    <button className={`px-4 py-2 rounded-lg font-medium ${variants[variant]}`}>
      {children}
    </button>
  );
}
```

## Avoid

- Inline styles (`style={{}}`)
- CSS modules when Tailwind suffices
- Deep nesting of utility classes
- Magic numbers (use theme values)
