# Security

Extensions run with elevated privileges and touch untrusted web pages. A bug can leak
user data across every site. Treat web pages and their content as hostile.

## 1. No remote code (MV3 CSP)

Manifest V3 forbids executing remote or string-built code. Don't try to work around it.

```typescript
// ❌ all rejected by the MV3 CSP / store review
eval(userInput);
new Function(code)();
const s = document.createElement('script'); s.src = 'https://cdn.example.com/x.js';
```

Bundle everything at build time. For dynamic config, fetch **data** (JSON), never code.

## 2. Validate message senders

Any web page can `runtime.sendMessage` to your extension if it knows the id. Validate the
sender before privileged actions.

```typescript
onMessage('deleteAll', async ({ sender }) => {
  // only accept messages from our own extension pages / content scripts
  if (sender.id !== browser.runtime.id) throw new Error('forbidden');
  // for content-script messages, optionally pin the origin
  if (sender.tab && !isAllowedOrigin(sender.origin)) throw new Error('forbidden');
  await wipe();
});
```

Scope `externally_connectable` narrowly (or omit it) so arbitrary sites can't talk to you.

## 3. Sanitise injected DOM

Never put page or user strings into `innerHTML`. Build nodes or let the framework render
(framework templating escapes by default).

```typescript
// ❌ XSS into your own extension UI / the page
el.innerHTML = `<div>${pageProvidedTitle}</div>`;

// ✅
el.textContent = pageProvidedTitle;
// or DOM APIs / React/Vue/Svelte rendering, which escape automatically
```

If you must render HTML, sanitise with a vetted library (e.g. DOMPurify) first.

## 4. Least-privilege permissions

Broad `host_permissions` and `<all_urls>` are the biggest risk and the biggest review
hurdle. Prefer `activeTab` + `scripting`, and `optional_permissions` requested at runtime.
See `patterns/permissions.md`.

## 5. Don't store secrets

Anything in `wxt/storage` or bundled into the extension is readable by a determined user
and, for content-script-accessible areas, by the page context. Do not embed API keys or
long-lived tokens. Authenticate against your backend and store short-lived,
revocable session tokens; do sensitive work server-side.

## 6. Isolate page interaction

- Use `ISOLATED` world content scripts by default; only use `MAIN` world when necessary
  and treat anything from it as untrusted.
- Validate `window.postMessage` data crossing the MAIN/ISOLATED boundary (check
  `event.origin` and `event.source`).
- Render injected UI in a shadow root so the page can't read or restyle it.

## 7. Network & data hygiene

- Use HTTPS endpoints only; validate/parse responses before use.
- Minimise the data you collect; be honest in the store privacy disclosure.
- Prefer `declarativeNetRequest` (declarative, no request bodies exposed) over observing
  raw traffic.

## Checklist

- [ ] No `eval` / `new Function` / remote scripts; data fetched, never code
- [ ] Message handlers validate `sender.id` / origin; `externally_connectable` is narrow
- [ ] No unsanitised page/user strings in `innerHTML`
- [ ] Least-privilege permissions; no `<all_urls>` without cause
- [ ] No secrets in storage/bundle; short-lived tokens only
- [ ] MAIN/ISOLATED boundary and `postMessage` data validated
