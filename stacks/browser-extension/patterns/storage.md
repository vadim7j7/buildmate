# Storage

Use `wxt/storage` for all persistence. It wraps `browser.storage` with typed items,
fallbacks, versioned migrations, and change watching — so you never sprinkle raw
`browser.storage.local.get('key')` calls through the codebase.

## 1. Define typed items

```typescript
// utils/storage.ts
import { storage } from 'wxt/storage';

export interface Settings {
  theme: 'light' | 'dark';
  enabled: boolean;
}

export const settings = storage.defineItem<Settings>('local:settings', {
  fallback: { theme: 'light', enabled: true },
  version: 1,
});
```

Keys are **namespaced by storage area**: `local:`, `sync:`, `session:`, `managed:`.

```typescript
const value = await settings.getValue();   // typed; returns fallback if unset
await settings.setValue({ theme: 'dark', enabled: true });
await settings.removeValue();
```

## 2. Choosing a storage area

| Area | Use for | Notes |
| --- | --- | --- |
| `local:` | Most app data | ~10 MB (more with `unlimitedStorage` permission) |
| `sync:` | Small user preferences synced across devices | ~100 KB total, ~8 KB/item, quota-limited |
| `session:` | In-memory, cleared when the browser closes | Not exposed to content scripts by default |
| `managed:` | Read-only policy set by enterprise admins | Cannot be written |

Don't put large or frequently-changing data in `sync:` — you'll hit `MAX_WRITE_OPERATIONS`
quotas. Keep secrets out of storage entirely (see `patterns/security.md`).

## 3. Watching for changes (reactive)

```typescript
const unwatch = settings.watch((newValue, oldValue) => {
  applyTheme(newValue.theme);
});
// later: unwatch();
```

In UI surfaces, attach the watcher on mount and detach on unmount (see
`styles/ui-react.md`). Watchers fire across contexts — a write in the popup updates the
content script live.

## 4. Versioned migrations

Bump `version` and add a `migrations` map when the stored shape changes. WXT runs the
migration the first time an item is read after the version increases.

```typescript
export const profile = storage.defineItem<ProfileV2>('local:profile', {
  fallback: { name: '', tags: [] },
  version: 2,
  migrations: {
    // migrate from v1 → v2
    2(old: { name: string; tag?: string }): ProfileV2 {
      return { name: old.name, tags: old.tag ? [old.tag] : [] };
    },
  },
});
```

## 5. Metadata and bulk operations

```typescript
// per-item metadata (e.g. timestamps)
await settings.setMeta({ lastSync: Date.now() });
const meta = await settings.getMeta();

// bulk
await storage.setItems([
  { item: settings, value: { theme: 'dark', enabled: true } },
]);
const [s] = await storage.getItems([settings]);
```

You can also use `storage.getItem('local:key')` / `storage.setItem` for ad-hoc keys, but
prefer `defineItem` so types and fallbacks live in one place.

## 6. Anti-patterns

```typescript
// ❌ raw, untyped, no fallback, scattered string keys
const { theme } = await browser.storage.local.get('theme');

// ❌ storing server data you should refetch, or secrets/tokens
// ❌ writing to sync: on every keystroke (quota errors)
```

## Checklist

- [ ] All persistence goes through `storage.defineItem` in `utils/storage.ts`
- [ ] Correct area chosen (`local`/`sync`/`session`/`managed`) with quotas in mind
- [ ] Shape changes ship a `version` bump + `migrations` entry
- [ ] UI watchers are detached on unmount
- [ ] No secrets in storage
