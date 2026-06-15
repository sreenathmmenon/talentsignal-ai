const { test, expect } = require('@playwright/test');

test.describe('TalentSignal live recruiter cockpit', () => {
  test('runs backend ranker from UI against real candidate data', async ({ page }) => {
    test.setTimeout(90000);
    await page.goto('http://127.0.0.1:8765/');
    await expect(page.getByRole('heading', { name: 'TalentSignal AI Recruiter Cockpit' })).toBeVisible();
    await page.selectOption('#topN', '25');
    await page.getByRole('button', { name: 'Run Ranker' }).click();
    await expect(page.locator('#status')).toContainText('Completed', { timeout: 70000 });
    await expect(page.locator('#results tr')).toHaveCount(25);
    await expect(page.locator('#results tr').first()).toContainText('CAND_');
    await expect(page.locator('#detail')).toContainText('Career retrieval/ranking');
    await expect(page.locator('#detail')).toContainText('Risk flags');
    await page.fill('#searchBox', 'AI Engineer');
    await expect(page.locator('#results tr').first()).toContainText('AI Engineer');
    await page.selectOption('#sortBy', 'confidence');
    await expect(page.locator('#results tr')).not.toHaveCount(0);
    await page.click('#resetBtn');
    await expect(page.locator('#results tr')).toHaveCount(25);
    await expect(page.locator('a[href="/download/ui_submission.csv"]')).toBeVisible();
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.locator('a[href="/download/ui_submission.csv"]').click(),
    ]);
    expect(download.suggestedFilename()).toBe('ui_submission.csv');
    await page.screenshot({ path: 'outputs/ui_playwright_desktop.png', fullPage: true });
  });

  test('renders responsive mobile layout after real ranking', async ({ page }) => {
    test.setTimeout(90000);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://127.0.0.1:8765/');
    await page.selectOption('#topN', '25');
    await page.getByRole('button', { name: 'Run Ranker' }).click();
    await expect(page.locator('#status')).toContainText('Completed', { timeout: 70000 });
    await expect(page.locator('#results tr')).toHaveCount(25);
    await expect(page.locator('#detail')).toContainText('Technical');
    await page.screenshot({ path: 'outputs/ui_playwright_mobile.png', fullPage: true });
  });
});
