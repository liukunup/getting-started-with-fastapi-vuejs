import { test, expect } from '@playwright/test';

test.describe('Applications', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.getByPlaceholder('Email address').fill('admin@example.com');
    await page.getByPlaceholder('Password').fill('changethis');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL('/');
    await page.goto('/applications');
  });

  test('should create, edit and delete an application', async ({ page }) => {
    const testAppName = `Test App ${Date.now()}`;
    const testDescription = 'This is a test application description';

    // Create Application
    await page.getByRole('button', { name: 'New' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    
    await page.fill('#name', testAppName);
    await page.fill('#description', testDescription);
    
    await page.getByRole('button', { name: 'Save' }).click();
    
    // Wait for App Key dialog (Specific to Applications)
    // In Applications.vue: if (response.app_key) { ... appKeyDialog.value = true; }
    // And toast: toast.add({ severity: 'success', summary: 'Successful', detail: 'Application Created', life: 3000 });
    
    // Check for App Key dialog
    const appKeyDialog = page.getByRole('dialog', { name: 'Application Created' });
    await expect(appKeyDialog).toBeVisible();
    await expect(page.getByText('Please save your App Key securely.')).toBeVisible();
    await appKeyDialog.getByRole('button', { name: 'Close' }).filter({ hasText: 'Close' }).click();
    await expect(appKeyDialog).toBeHidden();

    // Verify Application Created
    await page.getByPlaceholder('Search...').fill(testAppName);
    await expect(page.getByText(testAppName)).toBeVisible();

    // Edit Application
    await page.locator('.p-datatable-tbody button').filter({ has: page.locator('.pi-pencil') }).first().click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Change Description
    const newDescription = 'Updated app description';
    await page.fill('#description', newDescription);
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByText('Application Updated')).toBeVisible();
    await expect(page.getByRole('dialog')).toBeHidden();

    // Delete Application
    await page.locator('.p-datatable-tbody button').filter({ has: page.locator('.pi-trash') }).first().click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('Are you sure you want to delete')).toBeVisible();
    
    await page.getByRole('button', { name: 'Yes' }).click();
    
    // Wait for dialog to close
    await expect(page.getByRole('dialog')).toBeHidden();

    // Verify Application Deleted
    await expect(page.getByRole('cell', { name: testAppName })).toBeHidden();
  });
});
