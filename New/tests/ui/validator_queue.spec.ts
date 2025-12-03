import { test, expect } from '@playwright/test';

test.describe('Validator Queue UI', () => {
    test('should load validator page', async ({ page }) => {
        await page.goto('/validator');

        // Check page loaded
        await expect(page.locator('h1')).toContainText('Validator');

        // Check form exists
        await expect(page.locator('input, textarea').first()).toBeVisible();
    });

    test('should submit validation job', async ({ page }) => {
        await page.goto('/validator');

        // Fill in finding details
        await page.locator('input[placeholder*="ID"], input[name="findingId"]').fill('test-finding-ui-001');

        // Select type if dropdown exists
        const typeSelect = page.locator('select').first();
        await typeSelect.selectOption('reentrancy');

        // Fill title and description
        await page.locator('input[placeholder*="title"], input[name="title"]').fill('Test reentrancy');
        await page.locator('textarea').first().fill('Testing validator from UI');

        // Submit
        await page.locator('button:has-text("Submit"), button:has-text("Validate")').click();

        // Should show success message
        await expect(page.locator('text=/submitted|queued/i')).toBeVisible({ timeout: 10000 });
    });

    test('should display validation jobs', async ({ page }) => {
        await page.goto('/validator');

        // Jobs list should be visible
        await expect(page.locator('text=/Validation|Jobs/i')).toBeVisible();

        // May show empty state or existing jobs
        const hasJobs = await page.locator('text=/No validations|job/i').isVisible();
        expect(hasJobs).toBeTruthy();
    });

    test('should show job status', async ({ page }) => {
        await page.goto('/validator');

        // Submit a job
        await page.locator('input[name="findingId"], input[placeholder*="ID"]').fill('status-test');
        await page.locator('button:has-text("Submit")').click();

        // Wait for job to appear in list
        await page.waitForSelector('text=/status-test|queued|running/i', { timeout: 10000 });
    });
});
