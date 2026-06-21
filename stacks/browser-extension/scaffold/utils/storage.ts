import { storage } from 'wxt/storage';

// Typed, reactive storage items. Keys are namespaced by area: local: / sync: / session:.
// Bump `version` and add `migrations` when the shape changes. See patterns/storage.md
export interface Settings {
  theme: 'light' | 'dark';
  enabled: boolean;
}

export const settings = storage.defineItem<Settings>('local:settings', {
  fallback: { theme: 'light', enabled: true },
  version: 1,
});
