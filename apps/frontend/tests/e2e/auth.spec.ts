import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h1')).toContainText('Login');
  });

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/login');
    await page.click('text=Sign up');
    await expect(page).toHaveURL('/register');
  });

  test('should show validation errors on empty form submit', async ({ page }) => {
    await page.goto('/login');
    await page.click('button[type="submit"]');
    await expect(page.locator('.text-red-600')).toBeVisible();
  });
});

test.describe('Protected Routes', () => {
  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL('/login');
  });
});

test.describe('Chat', () => {
  test('should display chat page', async ({ page }) => {
    await page.goto('/chat');
    await expect(page.locator('input[type="text"]')).toBeVisible();
  });
});

test.describe('Navigation', () => {
  test('should display header navigation', async ({ page }) => {
    await page.goto('/chat');
    await expect(page.locator('nav')).toBeVisible();
  });
});
