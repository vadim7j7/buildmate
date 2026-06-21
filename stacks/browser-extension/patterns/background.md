# Background Service Worker

In Manifest V3 the background is a **service worker**: it has no DOM, no persistent
state, and is **terminated whenever it is idle** (~30s). Code defensively — treat every
event as if the worker just cold-started.

## 1. Event-driven, not stateful

WRONG — module-level state is lost when the worker is killed:

```typescript
let counter = 0; // ❌ resets to 0 every time the worker restarts
export default defineBackground(() => {
  browser.action.onClicked.addListener(() => {
    counter++; // unreliable
  });
});
```

CORRECT — persist with `wxt/storage`:

```typescript
import { storage } from 'wxt/storage';
const clicks = storage.defineItem<number>('local:clicks', { fallback: 0 });

export default defineBackground(() => {
  browser.action.onClicked.addListener(async () => {
    await clicks.setValue((await clicks.getValue()) + 1);
  });
});
```

## 2. Register listeners synchronously at the top level

MV3 dispatches events to a freshly-started worker. Listeners MUST be registered during
the initial synchronous run of `main()`, not inside a promise/`await`.

```typescript
export default defineBackground(() => {
  // ✅ registered synchronously — survives worker restarts
  browser.runtime.onMessage.addListener(handler);

  // ❌ registered after an await — the event may fire before this runs
  // const cfg = await loadConfig();
  // browser.runtime.onMessage.addListener(handler);
});
```

## 3. Use alarms, not setTimeout/setInterval

Long timers die with the worker. Use `browser.alarms` for anything beyond a few seconds.

```typescript
export default defineBackground(() => {
  browser.runtime.onInstalled.addListener(() => {
    browser.alarms.create('refresh', { periodInMinutes: 30 });
  });

  browser.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'refresh') void refreshData();
  });
});
```

Requires the `alarms` permission.

## 4. onInstalled / onStartup

```typescript
browser.runtime.onInstalled.addListener(({ reason }) => {
  if (reason === 'install') { /* first run: seed storage, open onboarding */ }
  if (reason === 'update') { /* run migrations */ }
});
browser.runtime.onStartup.addListener(() => { /* browser launched */ });
```

## 5. Message-routing hub

The background is the natural place to centralise privileged work. Pair it with typed
messaging (`patterns/messaging.md`) and **validate the sender** before acting
(`patterns/security.md`).

```typescript
import { onMessage } from '@/utils/messaging';

export default defineBackground(() => {
  onMessage('fetchJson', async ({ data }) => {
    const res = await fetch(data.url);
    return res.json();
  });
});
```

## 6. Context menus

```typescript
browser.runtime.onInstalled.addListener(() => {
  browser.contextMenus.create({ id: 'save', title: 'Save to My Extension', contexts: ['selection'] });
});
browser.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'save') void save(info.selectionText, tab?.id);
});
```

Requires the `contextMenus` permission.

## 7. Network interception: declarativeNetRequest

MV3 removed blocking `webRequest`. To block/modify/redirect requests, use
`declarativeNetRequest` with static rules (a JSON ruleset declared in the manifest) or
dynamic rules at runtime. Use observational `webRequest` only for read-only monitoring.

```typescript
await browser.declarativeNetRequest.updateDynamicRules({
  addRules: [{
    id: 1,
    priority: 1,
    action: { type: 'block' },
    condition: { urlFilter: '||ads.example.com', resourceTypes: ['script'] },
  }],
  removeRuleIds: [1],
});
```

## 8. Keep-alive: don't fight the lifecycle

Avoid hacks that ping the worker to keep it alive — they waste resources and stores may
reject them. If you have genuinely long work, use `alarms` to resume, persist progress to
storage, and make operations idempotent.

## Checklist

- [ ] No reliance on module-level mutable state across events
- [ ] All listeners registered synchronously in `main()`
- [ ] `alarms` instead of long timers; `declarativeNetRequest` instead of blocking webRequest
- [ ] Privileged handlers validate `sender`
