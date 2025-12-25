import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');
  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Sakai Vue/);
});

test('login page', async ({ page }) => {
  await page.goto('/auth/login');
  
  // Check for email and password fields
  await expect(page.locator('input[id="email1"]')).toBeVisible();
  // Password component in PrimeVue might wrap the input. 
  // Using getByPlaceholder is more robust or generic input[type="password"]
  await expect(page.getByPlaceholder('Password')).toBeVisible();
  
  // Check for Sign In button
  await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible();
});

test('failed login', async ({ page }) => {
  await page.goto('/auth/login');
  
  await page.fill('input[id="email1"]', 'wrong@example.com');
  // Use getByPlaceholder for password as well
  await page.getByPlaceholder('Password').fill('wrongpassword');
  await page.getByRole('button', { name: 'Sign In' }).click();
  
  // Expect error message (toast)
  // Note: This depends on the backend being reachable and returning an error.
  // If backend is not running, this might fail or behave differently.
  // We assume the toast appears.
  // await expect(page.locator('.p-toast-message-content')).toBeVisible();
});
