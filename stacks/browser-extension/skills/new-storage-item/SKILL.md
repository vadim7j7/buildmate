---
name: new-storage-item
description: Define a typed storage.defineItem with fallback, version, and migrations plus a reactive accessor
---

# /new-storage-item -- Define a Typed Storage Item

## What This Does

Creates a typed `storage.defineItem` in `utils/storage.ts` with a `fallback`
default, optional `version` + `migrations`, and a reactive accessor that watches
for changes. This is the only sanctioned way to persist extension state — never
call `browser.storage.local.get/set` directly in feature code.

## Usage

```
/new-storage-item settings                       # local:settings with a fallback
/new-storage-item theme --area=sync              # sync:theme (synced across devices)
/new-storage-item draft --area=session           # session:draft (cleared on browser close)
/new-storage-item settings --version=2           # with migrations from v1
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Item name in camelCase (also the storage key) |
| `--area` | No | `local` (default), `sync`, or `session` |
| `--version` | No | Schema version; enables migrations. Default: 1 |

## How It Works

### 1. Define the Item

Storage keys are namespaced by area: `'local:'`, `'sync:'`, `'session:'`. Always
provide a `fallback` so `getValue()` never returns `undefined`.

```typescript
// utils/storage.ts
import { storage } from 'wxt/storage';

export interface Settings {
  theme: 'light' | 'dark';
  notifications: boolean;
}

export const settings = storage.defineItem<Settings>('local:settings', {
  fallback: { theme: 'light', notifications: true },
});
```

Area guidance:

| Area | Use for |
|---|---|
| `local` | Default. Larger quota, device-local. |
| `sync` | Small user preferences synced across the signed-in browser. |
| `session` | Ephemeral state cleared when the browser closes (in-memory). |

### 2. Add Versioning + Migrations (when the shape changes)

When the stored shape evolves, bump `version` and add `migrations` keyed by the
target version. Each migration receives the previous value and returns the new
shape.

```typescript
export const settings = storage.defineItem<Settings>('local:settings', {
  fallback: { theme: 'light', notifications: true },
  version: 2,
  migrations: {
    // runs when upgrading stored data to v2
    2: (old: { theme: 'light' | 'dark' }): Settings => ({
      theme: old.theme,
      notifications: true,        // new field, sensible default
    }),
  },
});
```

WXT tracks the persisted version and runs the chain of migrations up to the
current `version` on first read after an update.

### 3. Reactive Accessor

Read, write, and watch for changes. `watch` returns an unwatch function — in a
content script, register it through `ctx`.

```typescript
import { settings } from '@/utils/storage';

// read (typed, always defined via fallback)
const current = await settings.getValue();

// write
await settings.setValue({ ...current, theme: 'dark' });

// reactive — fires on every change from any context
const unwatch = settings.watch((next, prev) => {
  applyTheme(next.theme);
});

// in a content script, tie it to ctx lifecycle
ctx.onInvalidated(unwatch);
```

### 4. Verify

```bash
npx wxt prepare && npx tsc --noEmit
npx vitest run
```

Test migrations with WXT's mocked storage:

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { fakeBrowser } from 'wxt/testing';
import { settings } from '@/utils/storage';

describe('settings', () => {
  beforeEach(() => fakeBrowser.reset());

  it('returns the fallback when unset', async () => {
    expect(await settings.getValue()).toEqual({
      theme: 'light',
      notifications: true,
    });
  });
});
```

## Conventions

- Always namespace the key with an area prefix (`local:`, `sync:`, `session:`).
- Always provide a `fallback` — never return `undefined`.
- Bump `version` and add a `migrations` entry whenever the shape changes; never
  silently change the type.
- Use `item.watch()` for reactivity instead of `browser.storage.onChanged`.
- Tie `watch` cleanup to `ctx` inside content scripts.

## Checklist

- [ ] Item defined in `utils/storage.ts` with an exported type
- [ ] Key namespaced with the correct area prefix
- [ ] `fallback` provided
- [ ] `version` + `migrations` added when evolving an existing item
- [ ] Reactive accessor (`watch`) used where state must stay in sync
- [ ] Migration test added; `tsc --noEmit` and `vitest run` pass
