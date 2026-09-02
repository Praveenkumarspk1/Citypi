import { test, expect } from '@playwright/test';

test.describe('POI Search', () => {
  test('should display map page', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
  });

  test('should search for POIs', async ({ page }) => {
    await page.goto('/');
    await page.fill('input[placeholder*="search"]', 'coffee');
    await page.press('input[placeholder*="search"]', 'Enter');
  });
});

test.describe('Transit', () => {
  test('should display transit page', async ({ page }) => {
    await page.goto('/transit');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Weather', () => {
  test('should display weather page', async ({ page }) => {
    await page.goto('/weather');
    await expect(page.locator('body')).toBeVisible();
  });
});
