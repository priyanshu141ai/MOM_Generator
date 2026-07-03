import { test, expect } from '@playwright/test';

test.describe('Read.ai Dashboard End-to-End Tests', () => {

  test('full workspace navigation and dashboard analytics flow', async ({ page }) => {
    // 1. Visit Dashboard
    await page.goto('http://127.0.0.1:8001/');
    
    // Check main title
    await expect(page.locator('aside h1')).toContainText('Read.ai Local');

    // 2. Create a Meeting
    const title = 'Sync of 18Y Experienced Coders';
    await page.locator('input[name="title"]').fill(title);
    await page.locator('input[name="meeting_url"]').fill('https://meet.google.com/xyz-pdq-abc');
    await page.locator('input[name="recipient_email"]').fill('lead@example.com');
    await page.getByRole('button', { name: 'Create Meeting' }).click();

    // Confirm meeting card/row appears in list
    const firstRow = page.locator('#rows tr').first();
    await expect(firstRow).toContainText('Sync of 18Y Experienced Coders');

    // 3. Open the meeting workspace details
    await firstRow.getByRole('button', { name: 'Open' }).click();
    await expect(page.locator('#meetingDetailSection')).toBeVisible();
    await expect(page.locator('#detailTitle')).toContainText('Sync of 18Y Experienced Coders');

    // 4. Test upload mock transcript (via API override for simplicity, or test UI tabs)
    // Click tabs to verify visibility transitions
    await page.getByRole('button', { name: '📝 Summary & MOM' }).click();
    await expect(page.locator('#tab-mom')).toBeVisible();
    await expect(page.locator('#momBox')).toContainText('MOM summary not generated yet');

    await page.getByRole('button', { name: '💬 Transcript' }).click();
    await expect(page.locator('#tab-transcript')).toBeVisible();
    await expect(page.locator('#transcriptBox')).toContainText('Transcript not generated yet');

    await page.getByRole('button', { name: '🎓 Speaker Coach' }).click();
    await expect(page.locator('#tab-coach')).toBeVisible();
    await expect(page.locator('#coachGrid')).toContainText('No analytics available yet');

    // 5. Navigate to Search Copilot
    await page.getByRole('button', { name: '🔍 Search Copilot' }).click();
    await expect(page.locator('#viewSearch')).toBeVisible();
    await page.locator('#searchInput').fill('Sync');
    await page.getByRole('button', { name: 'Search' }).click();
    await expect(page.locator('#searchResults')).toBeVisible();

    // 6. Navigate to Workspace Insights
    await page.getByRole('button', { name: '📊 Workspace Insights' }).click();
    await expect(page.locator('#viewInsights')).toBeVisible();
    await expect(page.locator('#globalTotalMeetings')).toContainText('1');
  });

});
