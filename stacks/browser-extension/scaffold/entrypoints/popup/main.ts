import { settings, type Settings } from '@/utils/storage';
import { sendMessage } from '@/utils/messaging';

// Vanilla popup that works under any --ui choice. If you selected react / vue / svelte,
// convert this surface with the `new-entrypoint` skill — the framework module is already
// configured in wxt.config.ts. See .claude/patterns/ui-surfaces.md
//
// style.css is loaded once, by the <link> in index.html.
//
// SECURITY: tab titles/URLs are page-controlled. Build DOM nodes and set textContent —
// never interpolate them into innerHTML. See .claude/patterns/security.md
const app = document.querySelector<HTMLDivElement>('#app')!;

const main = document.createElement('main');
main.className = 'popup';

const heading = document.createElement('h1');
heading.textContent = 'My Extension';

const tabTitle = document.createElement('p');
tabTitle.className = 'tab';

const toggle = document.createElement('button');
toggle.type = 'button';

main.append(heading, tabTitle, toggle);
app.replaceChildren(main);

function renderTheme(current: Settings) {
  toggle.textContent = `Theme: ${current.theme}`;
  document.documentElement.dataset.theme = current.theme;
}

toggle.addEventListener('click', async () => {
  const current = await settings.getValue();
  await settings.setValue({
    ...current,
    theme: current.theme === 'light' ? 'dark' : 'light',
  });
});

// Re-render whenever the setting changes (here or from another extension context).
settings.watch((next) => renderTheme(next));

async function init() {
  renderTheme(await settings.getValue());
  const tab = await sendMessage('getActiveTab', undefined);
  tabTitle.textContent = tab.title ?? 'No active tab';
}

init();
