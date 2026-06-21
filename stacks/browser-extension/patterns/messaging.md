# Messaging

Extension contexts (background, content scripts, popup, options, side panel) are isolated
and communicate by message passing. Use **typed** messaging via
[`@webext-core/messaging`](https://webext-core.aklinker1.io/) so the protocol is checked
at compile time.

## 1. Define one protocol

```typescript
// utils/messaging.ts
import { defineExtensionMessaging } from '@webext-core/messaging';

interface ProtocolMap {
  // method(data): returnType
  ping(): string;
  getActiveTab(): { id?: number; url?: string; title?: string };
  saveItem(data: { title: string; url: string }): { id: number };
}

export const { sendMessage, onMessage } = defineExtensionMessaging<ProtocolMap>();
```

## 2. Handle in the background

```typescript
// entrypoints/background.ts
import { onMessage } from '@/utils/messaging';

export default defineBackground(() => {
  onMessage('ping', () => 'pong');

  onMessage('saveItem', async ({ data, sender }) => {
    // validate the sender before doing privileged work — see patterns/security.md
    if (!sender.tab) throw new Error('unexpected sender');
    const id = await persist(data);
    return { id };
  });
});
```

The handler receives `{ data, sender }`. Returning a value (or a Promise) sends the
response back to the caller; throwing rejects the caller's `sendMessage` promise.

## 3. Call from anywhere

```typescript
// popup, options, or content script
import { sendMessage } from '@/utils/messaging';

const tab = await sendMessage('getActiveTab', undefined); // no-arg → pass undefined
const { id } = await sendMessage('saveItem', { title: document.title, url: location.href });
```

By default messages route to the background. To message a specific tab's content script,
pass the tab id as the third argument: `sendMessage('highlight', payload, tabId)`.

## 4. Long-lived connections (ports)

For streaming or stateful sessions, use a port instead of one-shot messages:

```typescript
// background
browser.runtime.onConnect.addListener((port) => {
  port.onMessage.addListener((msg) => port.postMessage({ echo: msg }));
});

// content script / popup
const port = browser.runtime.connect({ name: 'stream' });
port.onMessage.addListener((msg) => console.log(msg));
port.postMessage({ start: true });
```

## 5. Calling background functions directly (proxy-service)

When the background owns a service object and you want to call its methods from other
contexts without hand-writing message types, use
[`@webext-core/proxy-service`](https://webext-core.aklinker1.io/):

```typescript
// utils/data-service.ts
import { defineProxyService } from '@webext-core/proxy-service';

class DataService {
  async all() { /* ... */ }
}
export const [registerDataService, getDataService] =
  defineProxyService('DataService', () => new DataService());

// background: registerDataService();
// elsewhere:  await getDataService().all();
```

## 6. Raw API (when you can't add a dep)

```typescript
// receiver
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'PING') { sendResponse('pong'); }
  return true; // keep the channel open for an async sendResponse
});
// sender
const res = await browser.runtime.sendMessage({ type: 'PING' });
```

Prefer the typed API; the raw form loses type safety and the `return true` async footgun.

## 7. Errors and missing receivers

`sendMessage` rejects if no receiver is registered ("Receiving end does not exist") —
e.g. messaging a tab with no content script, or the worker not yet started. Wrap calls in
try/catch and handle the absent-receiver case.

## Checklist

- [ ] Single `ProtocolMap` in `utils/messaging.ts`; no untyped `runtime.sendMessage`
- [ ] Background handlers validate `sender` for privileged actions
- [ ] Async raw listeners `return true`; typed handlers just return/throw
- [ ] Ports used for streaming/stateful exchanges
- [ ] Callers handle the "no receiving end" rejection
