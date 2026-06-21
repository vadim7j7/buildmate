import { browser } from 'wxt/browser';
import { onMessage } from '@/utils/messaging';

// Background service worker. In Manifest V3 this is killed when idle — keep it
// event-driven and never rely on module-level state surviving. See patterns/background.md
export default defineBackground(() => {
  browser.runtime.onInstalled.addListener(({ reason }) => {
    if (reason === 'install') {
      console.log('Extension installed');
    }
  });

  // Typed message handlers — see utils/messaging.ts and patterns/messaging.md
  onMessage('ping', () => 'pong');

  onMessage('getActiveTab', async () => {
    const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
    return { id: tab?.id, url: tab?.url, title: tab?.title };
  });
});
