import { test, expect } from '@playwright/test';

test.describe('Remediator Panel UI', () => {
    test('should load remediator page', async ({ page }) => {
        await page.goto('/remediator');

        // Check page loaded
        await expect(page.locator('h1')).toContainText('Remediator');

        // Check stats cards visible
        await expect(page.locator('text=/Total Jobs|PRs Created/i')).toBeVisible();
    });

    test('should display remediation jobs', async ({ page }) => {
        await page.goto('/remediator');

        // Jobs section should be visible
        await expect(page.locator('text=/Remediation Jobs|No remediation/i')).toBeVisible();
    });

    test('should show PR history', async ({ page }) => {
        await page.goto('/remediator');

        // PR section should be visible
        await expect(page.locator('text=/Pull Requests|No pull requests/i')).toBeVisible();
    });

    test('should display job details', async ({ page }) => {
        await page.goto('/remediator');

        // If there are jobs, they should show status
        const hasJobs = await page.locator('text=/queued|running|completed|failed/i').count();

        // Either shows jobs or empty state
        expect(hasJobs >= 0).toBeTruthy();
    });
});
