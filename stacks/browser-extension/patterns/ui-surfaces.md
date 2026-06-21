# UI Surfaces

Extensions render UI in several places: the toolbar **popup**, the **options** page, a
**side panel**, a **new-tab** override, **devtools** panels, and **injected** UI inside web
pages (content scripts). Each is an entrypoint; share components and logic across them.

## 1. Popup

The toolbar dropdown. Short-lived — it is destroyed when it closes, so don't start long
timers or rely on in-memory state surviving.

```
entrypoints/popup/
  index.html      # <script type="module" src="./main.ts">
  main.ts         # or main.tsx for React
  style.css
```

Manifest: WXT sets `action.default_popup` automatically. Set a fixed `body { width }`.

## 2. Options page

Full settings UI. Declared via `entrypoints/options/`. Open it programmatically:

```typescript
await browser.runtime.openOptionsPage();
```

Prefer `options_ui` embedded mode (default) for a compact panel; use a full page for
complex settings.

## 3. Side panel (Chrome) / sidebar (Firefox)

A persistent panel alongside the page. Chrome uses `sidePanel`; Firefox uses
`sidebar_action`. Create `entrypoints/sidepanel/` and open it from a user gesture:

```typescript
// Chrome — must be called in response to a user gesture
browser.action.onClicked.addListener(async (tab) => {
  if ('sidePanel' in browser) {
    await browser.sidePanel.open({ tabId: tab.id! });
  }
});

// Allow opening via the toolbar icon
if ('sidePanel' in browser) {
  browser.sidePanel.setPanelBehavior?.({ openPanelOnActionClick: true });
}
```

See `patterns/cross-browser.md` for the per-browser manifest keys.

## 4. New tab / devtools

- `entrypoints/newtab/` overrides the new-tab page (`chrome_url_overrides.newtab`).
- `entrypoints/devtools/` adds a DevTools page that can register panels via
  `browser.devtools.panels.create(...)`.

## 5. Injected UI (content scripts)

To render UI **into a web page**, mount from a content script inside a shadow root so
host styles don't leak. See `patterns/content-scripts.md` §4 and, for React,
`styles/ui-react.md` §4.

## 6. Share code across surfaces

Keep surfaces thin and reuse:

```
components/      # shared presentational components
hooks/           # shared data hooks (storage, messaging)
utils/           # messaging, storage, formatting
entrypoints/
  popup/         # imports from components/ + hooks/
  options/       # imports from components/ + hooks/
  sidepanel/
```

All surfaces read the same `utils/storage.ts` items and `utils/messaging.ts` protocol, so
state stays consistent and a change in one surface reflects live in others (via
`storage.watch`).

## 7. Theming

Respect the user's color scheme with `color-scheme: light dark` and CSS variables, or read
a stored `theme` setting and apply a class. Keep theme in `wxt/storage` so every surface
shares it.

## Checklist

- [ ] Each surface is its own entrypoint folder; popup has a fixed width
- [ ] Shared UI in `components/`, data access in `hooks/`
- [ ] Side panel opened from a user gesture; cross-browser keys handled
- [ ] Injected page UI uses a shadow root
- [ ] Theme/state shared via `wxt/storage` watchers
