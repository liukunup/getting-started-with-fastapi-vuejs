import { test, expect } from '@playwright/test';

test.describe('Items', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.getByPlaceholder('Email address').fill('admin@example.com');
    await page.getByPlaceholder('Password').fill('changethis');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL('/');
    await page.goto('/items');
  });

  test('should create a new item', async ({ page }) => {
    await page.getByRole('button', { name: 'New' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    
    const testItemName = `Test Item ${Date.now()}`;
    await page.fill('#name', testItemName);
    await page.fill('#description', 'This is a test item description');
    
    await page.getByRole('button', { name: 'Save' }).click();
    
    // Wait for success toast
    await expect(page.getByText('Item Created')).toBeVisible();

    // Wait for dialog to close
    await expect(page.getByRole('dialog')).toBeHidden();
    
    // Search for the item
    await page.getByPlaceholder('Search...').fill(testItemName);

    // Verify item is in the table
    await expect(page.getByText(testItemName)).toBeVisible();
  });
});
