import { test, expect } from '@playwright/test';

test.describe('Guardrail Panel UI', () => {
    test('should load guardrail page', async ({ page }) => {
        await page.goto('/guardrail');

        // Check page loaded
        await expect(page.locator('h1')).toContainText('Guardrail');

        // Check for monitoring controls
        await expect(page.locator('input[placeholder*="0x"], input[placeholder*="contract"]')).toBeVisible();
    });

    test('should start monitoring', async ({ page }) => {
        await page.goto('/guardrail');

        // Fill contract address
        const addressInput = page.locator('input[placeholder*="0x"], input[placeholder*="contract"]').first();
        await addressInput.fill('0x1234567890123456789012345678901234567890');

        // Select chain
        const chainSelect = page.locator('select').first();
        await chainSelect.selectOption('ethereum');

        // Start monitoring
        await page.locator('button:has-text("Start")').click();

        // Should show success message
        await expect(page.locator('text=/monitoring|started/i')).toBeVisible({ timeout: 10000 });
    });

    test('should display active monitors', async ({ page }) => {
        await page.goto('/guardrail');

        // Start a monitor first
        await page.locator('input[placeholder*="0x"]').first().fill('0xabcdefabcdefabcdefabcdefabcdefabcdefabcd');
        await page.locator('button:has-text("Start")').click();

        // Wait for monitor to appear in list
        await page.waitForSelector('text=/Active|Monitoring/i', { timeout: 10000 });

        // Should show contract address in monitors list
        await expect(page.locator('text=/0xabcd/i')).toBeVisible();
    });

    test('should stop monitoring', async ({ page }) => {
        await page.goto('/guardrail');

        // Start monitoring
        await page.locator('input[placeholder*="0x"]').first().fill('0x9999999999999999999999999999999999999999');
        await page.locator('button:has-text("Start")').click();
        await page.waitForTimeout(2000);

        // Stop monitoring
        await page.locator('button:has-text("Stop")').first().click();

        // Should show stopped message
        await expect(page.locator('text=/stopped/i')).toBeVisible({ timeout: 5000 });
    });

    test('should create pause request', async ({ page }) => {
        await page.goto('/guardrail');

        // Navigate to pause requests section (may need to scroll)
        await page.locator('text=/Pause Request/i').scrollIntoViewIfNeeded();

        // Check pause request controls exist
        const pauseSection = page.locator('text=/pause/i').first();
        await expect(pauseSection).toBeVisible();
    });
});
