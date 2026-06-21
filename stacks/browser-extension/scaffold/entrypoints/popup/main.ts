import { settings } from '@/utils/storage';
import { sendMessage } from '@/utils/messaging';
import './style.css';

// Vanilla popup that works under any --ui choice. If you selected react / vue / svelte,
// convert this surface with the `new-entrypoint` skill — the framework module is already
// configured in wxt.config.ts. See patterns/ui-surfaces.md
const app = document.querySelector<HTMLDivElement>('#app')!;

async function render() {
  const current = await settings.getValue();
  const tab = await sendMessage('getActiveTab', undefined);

  app.innerHTML = `
    <main class="popup">
      <h1>My Extension</h1>
      <p class="tab">${tab.title ?? 'No active tab'}</p>
      <button id="toggle">Theme: ${current.theme}</button>
    </main>
  `;

  document.querySelector('#toggle')!.addEventListener('click', async () => {
    await settings.setValue({
      ...current,
      theme: current.theme === 'light' ? 'dark' : 'light',
    });
    render();
  });
}

render();
