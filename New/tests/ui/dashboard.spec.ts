import { test, expect } from '@playwright/test';

test.describe('Dashboard UI', () => {
    test('should load dashboard', async ({ page }) => {
        await page.goto('/');

        // Check main heading
        await expect(page.locator('h1, h2').first()).toBeVisible();

        // Check for dashboard elements
        await expect(page.locator('text=/Dashboard|Overview|Welcome/i')).toBeVisible();
    });

    test('should display navigation', async ({ page }) => {
        await page.goto('/');

        // Navigation should be visible
        await expect(page.locator('nav, [role="navigation"]')).toBeVisible();

        // Should have links to main features
        await expect(page.locator('a:has-text("Address"), a:has-text("Guardrail"), a:has-text("Validator")')).toHaveCount(3);
    });

    test('should show stats or metrics', async ({ page }) => {
        await page.goto('/');

        // Dashboard should show some stats
        const hasStats = await page.locator('text=/Total|Scans|Findings|Active/i').count();
        expect(hasStats > 0).toBeTruthy();
    });

    test('should navigate to address scanner', async ({ page }) => {
        await page.goto('/');

        // Click address scan link
        await page.locator('a:has-text("Address")').first().click();

        // Should navigate to address scan page
        await expect(page).toHaveURL(/\/address-scan/);
    });

    test('should navigate to guardrail', async ({ page }) => {
        await page.goto('/');

        // Click guardrail link
        await page.locator('a:has-text("Guardrail")').first().click();

        // Should navigate to guardrail page
        await expect(page).toHaveURL(/\/guardrail/);
    });
});
