import { test, expect } from '@playwright/test';

test('dashboard creates a meeting and escapes user content', async ({ page }) => {
  await page.goto('/');
  const title = '<img src=x onerror=alert(1)>';
  page.on('dialog', async dialog => {
    throw new Error(`Unexpected dialog: ${dialog.message()}`);
  });

  await page.locator('input[name="title"]').fill(title);
  await page.locator('input[name="meeting_url"]').fill('https://meet.google.com/abc-defg-hij');
  await page.locator('input[name="recipient_email"]').fill('test@example.com');
  await page.getByRole('button', { name: 'Create' }).click();

  await expect(page.getByText(title).first()).toBeVisible();
  await expect(page.locator('img[src="x"]')).toHaveCount(0);
});

test('calendar connect failure is visible and non-fatal', async ({ page }) => {
  await page.goto('/');
  const dialogPromise = page.waitForEvent('dialog');
  await page.getByRole('button', { name: 'Connect Calendar' }).click();
  const dialog = await dialogPromise;
    expect(dialog.message()).toContain('GOOGLE_CLIENT_ID');
    await dialog.accept();
  await expect(page.getByRole('heading', { name: 'Meetings', level: 2 })).toBeVisible();
});
