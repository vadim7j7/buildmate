---
name: new-message
description: Add a typed message to the @webext-core/messaging ProtocolMap and wire a background handler plus a caller
---

# /new-message -- Add a Typed Extension Message

## What This Does

Adds a new message to the `@webext-core/messaging` `ProtocolMap`, registers its
handler in the background entrypoint, and generates a typed caller. This keeps
all cross-context communication (popup → background, content → background, etc.)
fully type-checked end to end. Never dispatch on stringly-typed
`browser.runtime.sendMessage` payloads.

## Usage

```
/new-message getTabTitle                       # () => string
/new-message saveBookmark                       # ({url, title}) => boolean
/new-message fetchUser --args="{id: string}" --returns="User"
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Message name in camelCase verb form (e.g. `saveBookmark`) |
| `--args` | No | TypeScript type of the single data argument. Default: none |
| `--returns` | No | TypeScript return type. Default: `void` |

## How It Works

### 1. Ensure the Messaging Module Exists

If `utils/messaging.ts` doesn't exist yet, create it:

```typescript
// utils/messaging.ts
import { defineExtensionMessaging } from '@webext-core/messaging';

export interface ProtocolMap {
  // messages are added here
}

export const { sendMessage, onMessage } =
  defineExtensionMessaging<ProtocolMap>();
```

### 2. Add the Message to the ProtocolMap

Each entry is a method signature: `name(data: Args): ReturnType`. Omit the
parameter for no-arg messages.

```typescript
// utils/messaging.ts
export interface ProtocolMap {
  getTabTitle(): string;
  saveBookmark(data: { url: string; title: string }): boolean;
  fetchUser(data: { id: string }): User;
}
```

The return type may be a `Promise<T>` or a plain `T` — `sendMessage` always
resolves to a promise.

### 3. Register the Handler in the Background

Handlers must be registered at the top level of `defineBackground` so they're
ready before any message arrives.

```typescript
// entrypoints/background.ts
import { onMessage } from '@/utils/messaging';

export default defineBackground(() => {
  onMessage('saveBookmark', async ({ data }) => {
    // data is typed as { url: string; title: string }
    await persistBookmark(data);
    return true;             // checked against ProtocolMap return type
  });

  onMessage('getTabTitle', async ({ sender }) => {
    return sender.tab?.title ?? '';
  });
});
```

The handler callback receives `{ data, sender }`. `data` and the return type are
inferred from the `ProtocolMap`.

### 4. Call It from the Caller

```typescript
// e.g. entrypoints/popup/main.ts or a content script
import { sendMessage } from '@/utils/messaging';

const ok = await sendMessage('saveBookmark', {
  url: location.href,
  title: document.title,
});                          // ok: boolean

const title = await sendMessage('getTabTitle', undefined);
```

For no-arg messages, pass `undefined` as the data argument.

### 5. Verify

```bash
npx wxt prepare && npx tsc --noEmit
npx vitest run
```

A type error in either the handler or the caller means the signature doesn't
match the `ProtocolMap` — fix the map, not the call site.

## Conventions

- One `ProtocolMap` per extension, in `utils/messaging.ts`.
- Message names are camelCase verbs: `saveBookmark`, `getTabTitle`.
- Handlers live in the background entrypoint, registered at top level.
- Wrap caller `sendMessage` calls in try/catch where the context may go away.
- Never use raw `browser.runtime.sendMessage` with a `{ type, ... }` envelope.

## Checklist

- [ ] `utils/messaging.ts` exists with `defineExtensionMessaging<ProtocolMap>()`
- [ ] New message signature added to `ProtocolMap`
- [ ] `onMessage(name, handler)` registered in `defineBackground`
- [ ] At least one typed caller wired via `sendMessage`
- [ ] No-arg callers pass `undefined`
- [ ] `tsc --noEmit` and `vitest run` pass
