# shadcn/ui Style Guide

## Overview

Use shadcn/ui components built on Radix primitives + Tailwind CSS **v4**. Components
are copied into your project at `components/ui/`. Tailwind v4 is CSS-first: there is
no `tailwind.config.js`; tokens live in `globals.css` (see the Theme section and
`styles/tailwind.md` if installed).

## Installation

Initialize once, then add components via the `shadcn` CLI (the old `shadcn-ui` package is deprecated):

```bash
npx shadcn@latest init
npx shadcn@latest add button card input
```

`init` writes `components.json` (with `"tailwind": { "config": "", "css": "src/app/globals.css", ... }`:
an empty `config` means Tailwind v4), the `cn()` helper in `lib/utils.ts`, and the theme
variables in `globals.css`. Animations come from `tw-animate-css` (`tailwindcss-animate`
is the v3 plugin; don't add it).

## Component Usage

Import from local `components/ui`:

```tsx
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
```

## Common Components

### Button

```tsx
<Button>Default</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
<Button disabled>Disabled</Button>
```

### Card

```tsx
<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Card content</p>
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

### Form

```tsx
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"

const form = useForm<FormData>({
  resolver: zodResolver(schema),
  defaultValues: { email: "" },
})

<Form {...form}>
  <form onSubmit={form.handleSubmit(onSubmit)}>
    <FormField
      control={form.control}
      name="email"
      render={({ field }) => (
        <FormItem>
          <FormLabel>Email</FormLabel>
          <FormControl>
            <Input {...field} />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
    <Button type="submit">Submit</Button>
  </form>
</Form>
```

### Dialog (Modal)

```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

<Dialog>
  <DialogTrigger asChild>
    <Button>Open Dialog</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Are you sure?</DialogTitle>
      <DialogDescription>
        This action cannot be undone.
      </DialogDescription>
    </DialogHeader>
    <div className="flex justify-end gap-2">
      <Button variant="outline">Cancel</Button>
      <Button variant="destructive">Delete</Button>
    </div>
  </DialogContent>
</Dialog>
```

### Toast Notifications

The old `toast` / `useToast` component is deprecated; use Sonner
(`npx shadcn@latest add sonner`):

```tsx
// app/layout.tsx: render once
import { Toaster } from "@/components/ui/sonner"
// ... <body>{children}<Toaster /></body>

// anywhere in a Client Component
import { toast } from "sonner"

toast.success("Your changes have been saved.")
toast.error("Something went wrong.")
```

## Customization

Edit component files directly in `components/ui/`. The source is yours.

To change the default variant of a Button:

```tsx
// components/ui/button.tsx
const buttonVariants = cva(
  "...",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        // Add custom variants here
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)
```

## Theme

Colors are CSS variables in `globals.css` (OKLCH), mapped to Tailwind utilities with
`@theme inline`, so `bg-primary`, `text-muted-foreground` etc. follow light/dark:

```css
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

:root {
  --radius: 0.625rem;
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  --primary-foreground: oklch(0.985 0 0);
  /* ... */
}

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --primary: oklch(0.922 0 0);
  --primary-foreground: oklch(0.205 0 0);
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --radius-lg: var(--radius);
}
```

Add a new token in all three places (`:root`, `.dark`, `@theme inline`). Old
HSL-triplet themes (`--primary: 222.2 47.4% 11.2%` + `hsl(var(--primary))`) are the
Tailwind v3 setup; don't copy them into a v4 project.

## Best Practices

1. **Use the CLI** to add components rather than copying manually
2. **Keep components in sync** - when you update shadcn, update your components
3. **Customize in place** - edit the component files directly
4. **Compose components** - build complex UIs from simple primitives
5. **Use Radix primitives** for accessibility
