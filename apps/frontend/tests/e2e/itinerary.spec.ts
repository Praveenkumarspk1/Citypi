import { test, expect } from '@playwright/test';

test.describe('Itinerary', () => {
  test('should display itinerary page', async ({ page }) => {
    await page.goto('/itinerary');
    await expect(page.locator('body')).toBeVisible();
  });

  test('should create new itinerary', async ({ page }) => {
    await page.goto('/itinerary');
    await page.click('text=Create Itinerary');
    await expect(page.locator('input[placeholder*="title"]')).toBeVisible();
  });
});
