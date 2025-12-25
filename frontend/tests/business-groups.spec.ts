import { test, expect } from '@playwright/test';

test.describe('Groups', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.getByPlaceholder('Email address').fill('admin@example.com');
    await page.getByPlaceholder('Password').fill('changethis');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL('/');
    await page.goto('/groups');
  });

  test('should create, edit and delete a group', async ({ page }) => {
    const testGroupName = `Test Group ${Date.now()}`;
    const testDescription = 'This is a test group description';

    // Create Group
    await page.getByRole('button', { name: 'New' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    
    await page.fill('#name', testGroupName);
    await page.fill('#description', testDescription);
    
    await page.getByRole('button', { name: 'Save' }).click();
    
    // Wait for success toast
    await expect(page.getByText('Group Created')).toBeVisible();
    await expect(page.getByRole('dialog')).toBeHidden();

    // Verify Group Created
    await page.getByPlaceholder('Search...').fill(testGroupName);
    await expect(page.getByText(testGroupName)).toBeVisible();

    // Edit Group
    await page.locator('.p-datatable-tbody button').filter({ has: page.locator('.pi-pencil') }).first().click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Change Description
    const newDescription = 'Updated description';
    await page.fill('#description', newDescription);
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByText('Group Updated')).toBeVisible();
    await expect(page.getByRole('dialog')).toBeHidden();

    // Delete Group
    await page.locator('.p-datatable-tbody button').filter({ has: page.locator('.pi-trash') }).first().click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(`Are you sure you want to delete ${testGroupName}?`)).toBeVisible();
    
    await page.getByRole('button', { name: 'Yes' }).click();
    
    // Wait for dialog to close
    await expect(page.getByRole('dialog')).toBeHidden();

    // Verify Group Deleted
    await expect(page.getByRole('cell', { name: testGroupName })).toBeHidden();
  });
});
