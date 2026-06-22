const { test, expect } = require('@playwright/test');

const UI_URL = process.env.TALENTSIGNAL_UI_URL || 'http://127.0.0.1:8765/';

test.describe('TalentSignal live recruiter cockpit', () => {
  test('generates shortlist from UI against candidate data', async ({ page }) => {
    test.setTimeout(90000);
    await page.goto(UI_URL);
    await expect(page.getByRole('heading', { name: 'Evidence-backed hiring decisions for any role.' })).toBeVisible();
    await expect(page.locator('.ts-sidebar')).toBeVisible();
    await expect(page.locator('.ts-sidebar')).toContainText('Role Intelligence');
    await expect(page.locator('.ts-sidebar')).toContainText('Interview Kit');
    await page.selectOption('#topN', '25');
    await page.getByRole('button', { name: 'Generate Shortlist' }).click();
    await expect(page.locator('#status')).toContainText('Scoring candidate evidence', { timeout: 12000 });
    await expect(page.locator('#status')).toContainText('Completed', { timeout: 70000 });
    await expect(page.locator('#roleIntel')).toContainText('Senior AI Engineer');
    await expect(page.locator('#decisionFramework')).toContainText('technical evidence');
    await expect(page.locator('#compareMode')).toContainText('Recommendation');
    await expect(page.locator('#trustLayer')).toContainText('Top-10 risk pressure');
    await expect(page.locator('#interviewKit')).toContainText('Technical depth');
    await expect(page.locator('#boundaryReview')).toContainText('top 10 boundary');
    await expect(page.locator('#universalProof')).toContainText('Current scorecard');
    await page.selectOption('#compareLeft', '10');
    await page.selectOption('#compareRight', '11');
    await expect(page.locator('#compareMode')).toContainText('#10');
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

  test('renders responsive mobile layout after shortlist generation', async ({ page }) => {
    test.setTimeout(90000);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(UI_URL);
    await page.selectOption('#topN', '25');
    await page.getByRole('button', { name: 'Generate Shortlist' }).click();
    await expect(page.locator('#status')).toContainText('Completed', { timeout: 70000 });
    await expect(page.locator('#results tr')).toHaveCount(25);
    await expect(page.locator('#detail')).toContainText('Technical');
    await page.screenshot({ path: 'outputs/ui_playwright_mobile.png', fullPage: true });
  });
});
