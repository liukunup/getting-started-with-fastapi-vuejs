import { test, expect } from '@playwright/test';

test.describe('Profile', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.getByPlaceholder('Email address').fill('admin@example.com');
    await page.getByPlaceholder('Password').fill('changethis');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL('/');
    await page.goto('/profile');
  });

  test('should update profile full name', async ({ page }) => {
    await page.getByRole('button', { name: 'Edit Profile' }).click();
    
    const newFullName = `Admin User ${Date.now()}`;
    await page.fill('#full_name', newFullName);
    
    await page.getByRole('button', { name: 'Save' }).click();
    
    // Wait for success toast
    await expect(page.getByText('Profile updated successfully')).toBeVisible();
    
    // Verify the name is updated in the view (non-edit mode)
    await expect(page.locator('#full_name')).toHaveValue(newFullName);
  });
});
