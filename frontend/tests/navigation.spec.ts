import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.getByPlaceholder('Email address').fill('admin@example.com');
    await page.getByPlaceholder('Password').fill('changethis');
    await page.getByRole('button', { name: 'Sign In' }).click();
    // Wait for navigation to dashboard
    await expect(page).toHaveURL('/');
  });

  test('should navigate to dashboard', async ({ page }) => {
    // Check for StatsWidget content
    await expect(page.getByText('Orders', { exact: true })).toBeVisible();
    await expect(page.getByText('Revenue', { exact: true })).toBeVisible();
  });

  test('should navigate to items', async ({ page }) => {
    await page.goto('/items');
    await expect(page).toHaveURL('/items');
    await expect(page.getByRole('heading', { name: 'Manage Items' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'New' })).toBeVisible();
  });

  test('should navigate to profile', async ({ page }) => {
    await page.goto('/profile');
    await expect(page).toHaveURL('/profile');
    await expect(page.getByRole('heading', { name: 'Profile Settings' })).toBeVisible();
  });
});
