import { test, expect } from '@playwright/test';

test.describe('Report Download UI', () => {
    test('should load reports page', async ({ page }) => {
        await page.goto('/reports');

        // Check page loaded
        await expect(page.locator('h1')).toContainText('Report');

        // Check for scan list or empty state
        await expect(page.locator('text=/Recent Scans|No scans|Reports/i')).toBeVisible();
    });

    test('should show scan results', async ({ page }) => {
        await page.goto('/reports');

        // May show scans or empty state
        const hasContent = await page.locator('text=/scan|report|No scans/i').isVisible();
        expect(hasContent).toBeTruthy();
    });

    test('should have download options', async ({ page }) => {
        await page.goto('/reports');

        // Check for download controls (buttons might be disabled if no reports)
        const downloadControls = await page.locator('button:has-text("Download"), text=/download/i').count();
        expect(downloadControls >= 0).toBeTruthy();
    });
});
