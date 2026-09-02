import { test, expect } from '@playwright/test';

test.describe('Visual Regression', () => {
  test('login page visual', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveScreenshot('login-page.png');
  });

  test('chat page visual', async ({ page }) => {
    await page.goto('/chat');
    await expect(page).toHaveScreenshot('chat-page.png');
  });

  test('map page visual', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveScreenshot('map-page.png');
  });

  test('transit page visual', async ({ page }) => {
    await page.goto('/transit');
    await expect(page).toHaveScreenshot('transit-page.png');
  });

  test('weather page visual', async ({ page }) => {
    await page.goto('/weather');
    await expect(page).toHaveScreenshot('weather-page.png');
  });

  test('profile page visual', async ({ page }) => {
    await page.goto('/profile');
    await expect(page).toHaveScreenshot('profile-page.png');
  });
});
