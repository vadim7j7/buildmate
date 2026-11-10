import { test, expect } from './fixtures';

test('popup renders and toggles the theme', async ({ page, extensionId }) => {
  await page.goto(`chrome-extension://${extensionId}/popup.html`);

  const toggle = page.getByRole('button', { name: /Theme:/ });
  await expect(toggle).toHaveText('Theme: light');
  await toggle.click();
  await expect(toggle).toHaveText('Theme: dark');
});
