---
name: new-context
description: Generate a new React Context with Provider, custom hook, and TypeScript types
---

# /new-context

## What This Does

Creates a new React Context with a typed Provider component, `useMemo`-optimized
value, `useCallback` handlers, and a custom hook with an `undefined` safety
check.

## Usage

```
/new-context Auth
/new-context Theme
/new-context Workspace
/new-context Notifications
```

## How It Works

### 1. Determine Context Shape

Based on the context name, infer:
- What state values are needed
- What actions/handlers are needed
- What the provider needs to wrap

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` for conventions
- `skills/new-context/references/context-examples.md` for examples
- Existing contexts in `src/contexts/` for project patterns

### 3. Generate Files

#### Context: `src/contexts/<Name>Context.tsx`

```typescript
'use client';

import { createContext, useContext, useState, useMemo, useCallback, type ReactNode } from 'react';

type <Name>ContextValue = {
  // state and handlers
};

const <Name>Context = createContext<<Name>ContextValue | undefined>(undefined);

export function <Name>Provider({ children }: { children: ReactNode }) {
  // state
  // handlers wrapped in useCallback
  // value wrapped in useMemo

  return <<Name>Context.Provider value={value}>{children}</<Name>Context.Provider>;
}

export function use<Name>() {
  const context = useContext(<Name>Context);
  if (context === undefined) {
    throw new Error('use<Name> must be used within a <Name>Provider');
  }
  return context;
}
```

#### Test: `src/contexts/<Name>Context.test.tsx`

Tests for provider rendering, hook access, and state updates.

### 4. Verify

Run `npx tsc --noEmit` to verify the context compiles.

## Rules

- All contexts use `'use client'` directive
- Context value type includes `| undefined` for the `createContext` call
- Custom hook throws if used outside Provider
- Provider value wrapped in `useMemo` to prevent unnecessary re-renders
- Event handlers wrapped in `useCallback`
- Use `type` for context value (not `interface`)
- Named exports for Provider and hook

## Output

```
Created:
  src/contexts/<Name>Context.tsx       -- Context, Provider, and hook
  src/contexts/<Name>Context.test.tsx  -- Unit tests

Verified:
  npx tsc --noEmit  -- PASS
```
