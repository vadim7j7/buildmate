---
name: new-component
description: Generate a new React component with TypeScript and test file
---

# /new-component

## What This Does

Creates a new React component following project conventions: TypeScript props
with `type`, proper Server/Client designation, and a co-located test file.
Uses the project's configured UI library for components.

## Usage

```
/new-component ProfileCard
/new-component SearchBar
/new-component ProjectStatusBadge
/new-component ConfirmDialog
```

## How It Works

### 1. Analyze Requirements

Determine from the component name and context:
- Is this a **Server Component** (presentational, no interactivity)?
- Is this a **Client Component** (hooks, events, state)?
- What UI components from the project's configured library are appropriate?
- What props does it need?

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` for code conventions
- `skills/new-component/references/component-examples.md` for examples
- The project's UI library style guide (in `styles/`) for component usage
- Existing components in `src/components/` for project-specific patterns

### 3. Generate Files

Create two files:

#### Component File: `src/components/<Name>.tsx`

```typescript
// 'use client' only if needed

type <Name>Props = {
  // typed props
};

export function <Name>({ prop1, prop2 }: <Name>Props) {
  return (
    // Use the project's UI library components
  );
}
```

#### Test File: `src/components/<Name>.test.tsx`

```typescript
import { render, screen } from '@testing-library/react';
import { <Name> } from './<Name>';

describe('<Name>', () => {
  const defaultProps = {
    // sensible defaults for all required props
  };

  it('renders without crashing', () => {
    render(<<Name> {...defaultProps} />);
    // assertion on visible content
  });

  it('displays expected content', () => {
    render(<<Name> {...defaultProps} />);
    // content assertions
  });
});
```

### 4. Verify

Run `npx tsc --noEmit` to verify the component compiles without errors.

## Rules

- Use `type` for props (NOT `interface`)
- Use named exports (NOT default exports)
- Use the project's configured UI library components (see style guides)
- Add `'use client'` only when the component uses hooks, events, or browser APIs
- Props type name follows `<ComponentName>Props` convention
- Include JSDoc comment on the component explaining its purpose
- Test file covers at minimum: renders without crashing, displays key content

## Output

```
Created:
  src/components/<Name>.tsx       -- Component implementation
  src/components/<Name>.test.tsx  -- Unit tests

Verified:
  npx tsc --noEmit  -- PASS
```
