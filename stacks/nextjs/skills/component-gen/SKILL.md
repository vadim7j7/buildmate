---
name: component-gen
description: Quick component generation for React + Next.js with Mantine UI and TypeScript
---

# /component-gen

## What This Does

Quickly generates a React component scaffold with TypeScript types, Mantine UI,
and proper Server/Client component designation. Useful for rapid prototyping
when you need a component fast without the full new-component workflow.

## Usage

```
/component-gen Button variant:filled|outline size:sm|md|lg
/component-gen DataTable columns:name,email,status
/component-gen Modal title:string onClose:function children:ReactNode
/component-gen Card title:string description:string image?:string
```

## How It Works

### 1. Parse Input

Extract:
- **Component name** (PascalCase)
- **Props** with types (from key:type pairs)
- **Client or Server** determination based on props/behavior

### 2. Determine Component Type

| Indicator | Component Type |
|---|---|
| Event handler props (onClick, onSubmit, onChange) | Client (`'use client'`) |
| State-related props (isOpen, isLoading) | Client (`'use client'`) |
| Data display only (title, description, items) | Server (default) |
| Form elements | Client (`'use client'`) |

### 3. Generate Component

Create the component file at `src/components/<Name>.tsx`:

#### Server Component Template

```typescript
import { Card, Text, Stack } from '@mantine/core';

type {{Name}}Props = {
  // generated from input
};

export function {{Name}}({ ...props }: {{Name}}Props) {
  return (
    // Mantine UI layout
  );
}
```

#### Client Component Template

```typescript
'use client';

import { useState } from 'react';
import { Button, Modal, Stack } from '@mantine/core';

type {{Name}}Props = {
  // generated from input
};

export function {{Name}}({ ...props }: {{Name}}Props) {
  // state and event handlers
  return (
    // Mantine UI layout
  );
}
```

### 4. Generate Test File

Create `src/components/<Name>.test.tsx` with a basic render test:

```typescript
import { render, screen } from '@testing-library/react';
import { {{Name}} } from './{{Name}}';

describe('{{Name}}', () => {
  it('renders without crashing', () => {
    render(<{{Name}} /* required props */ />);
    // basic assertion
  });
});
```

## Rules

- Use `type` for props (not `interface`)
- Use Mantine UI components (not raw HTML)
- Use named exports
- Add `'use client'` only when needed
- Include all required props as non-optional
- Include sensible defaults for optional props
- Generate a co-located test file

## Output

Reports which files were created:

```
Created:
  src/components/{{Name}}.tsx
  src/components/{{Name}}.test.tsx
```
