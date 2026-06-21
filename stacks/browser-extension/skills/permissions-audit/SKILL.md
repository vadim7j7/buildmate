---
name: permissions-audit
description: Audit wxt.config.ts manifest permissions and host_permissions for least-privilege, flag over-broad grants, and suggest optional_permissions with runtime requests
---

# /permissions-audit -- Audit Extension Permissions

## What This Does

Reviews the `permissions`, `host_permissions`, and `optional_permissions`
declared in `wxt.config.ts` against what the code actually uses. It flags unused
and over-broad grants, cross-checks content-script `matches` against
`host_permissions`, and recommends moving rarely-used grants to
`optional_permissions` with runtime requests. Least privilege reduces store
review friction and the install-time permission warning users see.

## Usage

```
/permissions-audit                     # full audit of wxt.config.ts + code
/permissions-audit --fix               # also apply safe least-privilege edits
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--fix` | No | Apply safe narrowing edits (remove unused, tighten hosts) |

## How It Works

### 1. Read the Declared Permissions

Parse the manifest block in `wxt.config.ts`:

```typescript
// wxt.config.ts
import { defineConfig } from 'wxt';

export default defineConfig({
  manifest: {
    permissions: ['storage', 'tabs', 'scripting', 'activeTab'],
    host_permissions: ['<all_urls>'],
    optional_permissions: [],
  },
});
```

Also collect every content-script `matches` array from `entrypoints/*content*`.

### 2. Cross-Reference Against Code Usage

For each declared permission, search the codebase for the API that requires it.
A grant with no corresponding call is **unused**.

| Permission | Required by (search for) |
|---|---|
| `storage` | `wxt/storage` items, `browser.storage.*` |
| `tabs` | `browser.tabs.*` (URL/title access; `activeTab` may suffice) |
| `scripting` | `browser.scripting.executeScript` |
| `activeTab` | on-click access to the current tab (preferred over `tabs` + `<all_urls>`) |
| `cookies` | `browser.cookies.*` |
| `contextMenus` | `browser.contextMenus.*` |
| `notifications` | `browser.notifications.*` |
| `webRequest` | `browser.webRequest.*` |
| `sidePanel` | side panel entrypoint / `browser.sidePanel.*` |
| `alarms` | `browser.alarms.*` |

Use the tools available to grep, e.g.:

```bash
rg "browser\.tabs\." entrypoints utils components
rg "browser\.scripting\.executeScript" entrypoints
```

### 3. Flag Findings

Report each issue with severity:

- **Unused** — declared but no matching API call. Remove it.
- **Over-broad host** — `host_permissions: ['<all_urls>']` or
  `'*://*/*'` when the code only touches specific origins. Narrow to the real
  origins, matching the content-script `matches`.
- **`tabs` vs `activeTab`** — if tab access is only needed in response to a user
  action, prefer `activeTab` (no host warning) over `tabs` + broad hosts.
- **Rarely used** — a powerful permission (`cookies`, `webRequest`, `history`)
  used behind an opt-in feature. Move to `optional_permissions` and request at
  runtime.
- **Mismatch** — `host_permissions` broader than the union of content-script
  `matches`.

### 4. Recommend Least-Privilege Fixes

```typescript
// BEFORE — over-broad
manifest: {
  permissions: ['tabs', 'storage', 'cookies'],
  host_permissions: ['<all_urls>'],
}

// AFTER — least privilege
manifest: {
  permissions: ['activeTab', 'storage'],
  host_permissions: ['*://*.github.com/*'],
  optional_permissions: ['cookies'],          // opt-in feature only
  optional_host_permissions: ['*://*.example.com/*'],
}
```

Request optional permissions at runtime, gated on the user action that needs them:

```typescript
import { browser } from 'wxt/browser';

async function enableCookieSync(): Promise<boolean> {
  const granted = await browser.permissions.request({
    permissions: ['cookies'],
    origins: ['*://*.example.com/*'],
  });
  if (!granted) return false;
  // proceed using browser.cookies.*
  return true;
}
```

### 5. Verify

After any edit, rebuild to confirm the manifest is still valid and the code
still type-checks:

```bash
npx wxt prepare && npx tsc --noEmit
npx wxt build && npx wxt build -b firefox
```

## Conventions

- Prefer `activeTab` over `tabs` + broad `host_permissions` whenever access is
  user-initiated.
- Scope `host_permissions` to exact origins; reserve `<all_urls>` for genuine
  universal scrapers and justify it.
- Keep `host_permissions` no broader than the union of content-script `matches`.
- Put any permission behind an opt-in feature in `optional_permissions` and
  request it at runtime with `browser.permissions.request`.
- Never request a permission "just in case" — it inflates the install warning.

## Audit Report Format

```
## Permissions Audit

**permissions:** [storage, tabs, scripting, activeTab]
**host_permissions:** [<all_urls>]

### Findings
- [HIGH] host_permissions '<all_urls>' — code only touches github.com.
  → Narrow to '*://*.github.com/*'.
- [MED] 'tabs' — only used on toolbar click. → Replace with 'activeTab'.
- [MED] 'cookies' — used by optional sync feature. → Move to optional_permissions.
- [LOW] 'scripting' — no browser.scripting.* call found. → Remove if unused.

### Recommended wxt.config.ts
<diff>
```

## Checklist

- [ ] Every declared permission maps to a real API call
- [ ] `host_permissions` scoped to exact origins (no needless `<all_urls>`)
- [ ] `host_permissions` ⊇ but not broader than content-script `matches`
- [ ] `activeTab` preferred over `tabs` for user-initiated access
- [ ] Opt-in features use `optional_permissions` + runtime `permissions.request`
- [ ] `wxt build` (Chrome + Firefox) passes after edits
