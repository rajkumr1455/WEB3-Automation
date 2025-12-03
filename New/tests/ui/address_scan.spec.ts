import { test, expect } from '@playwright/test';

test.describe('Address Scanner UI', () => {
    test('should load address scan page', async ({ page }) => {
        await page.goto('/address-scan');

        // Check page title
        await expect(page.locator('h1')).toContainText('Address');

        // Check form elements exist
        await expect(page.locator('input[placeholder*="0x"]')).toBeVisible();
        await expect(page.locator('button:has-text("Scan")')).toBeVisible();
    });

    test('should submit address scan', async ({ page }) => {
        await page.goto('/address-scan');

        // Fill in address
        const addressInput = page.locator('input[placeholder*="0x"]');
        await addressInput.fill('0x6B175474E89094C44Da98b954EedeAC495271d0F');

        // Submit form
        await page.locator('button:has-text("Scan")').click();

        // Should show loading/processing state
        await expect(page.locator('text=/scanning|processing/i')).toBeVisible({ timeout: 5000 });
    });

    test('should display scan results', async ({ page }) => {
        await page.goto('/address-scan');

        // Submit scan
        await page.locator('input[placeholder*="0x"]').fill('0x6B175474E89094C44Da98b954EedeAC495271d0F');
        await page.locator('button:has-text("Scan")').click();

        // Wait for results (or error message about API keys)
        await page.waitForSelector('text=/completed|error|No verified/i', { timeout: 30000 });
    });

    test('should handle invalid address', async ({ page }) => {
        await page.goto('/address-scan');

        // Enter invalid address
        await page.locator('input[placeholder*="0x"]').fill('invalid');
        await page.locator('button:has-text("Scan")').click();

        // Should show error
        await expect(page.locator('text=/invalid|error/i')).toBeVisible({ timeout: 5000 });
    });

    test('should show chain selector', async ({ page }) => {
        await page.goto('/address-scan');

        // Chain selector should be visible
        const chainSelect = page.locator('select, [role="combobox"]').first();
        await expect(chainSelect).toBeVisible();
    });
});
