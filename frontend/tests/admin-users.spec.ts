import { test, expect } from '@playwright/test';

test.describe('Admin Users', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.getByPlaceholder('Email address').fill('admin@example.com');
    await page.getByPlaceholder('Password').fill('changethis');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL('/');
    await page.goto('/admin/users');
  });

  test('should create, edit and delete a user', async ({ page }) => {
    const testEmail = `testuser${Date.now()}@example.com`;
    const testPassword = 'testpassword123';

    // Create User
    await page.getByRole('button', { name: 'New' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    
    await page.fill('#email', testEmail);
    await page.fill('#password', testPassword);
    
    // Select Role (assuming 'user' role exists and is selectable)
    // PrimeVue Select component interaction might be tricky. 
    // We click the dropdown trigger, then select the option.
    await page.click('#role');
    await page.getByRole('option', { name: 'user' }).click();

    await page.getByRole('button', { name: 'Save' }).click();
    
    // Wait for success toast
    await expect(page.getByText('User Created')).toBeVisible();
    await expect(page.getByRole('dialog')).toBeHidden();

    // Verify User Created
    await page.getByPlaceholder('Search...').fill(testEmail);
    await expect(page.getByText(testEmail)).toBeVisible();

    // Edit User
    // We need to find the edit button for this specific user.
    // Since we filtered by email, it should be the only/first row.
    // Use a more robust selector for the edit button (PrimeVue button with pencil icon)
    // Scope to the table body to avoid toolbar buttons
    await page.locator('.p-datatable-tbody button').filter({ has: page.locator('.pi-pencil') }).first().click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Change Active status
    await page.locator('label[for="is_active"]').click(); // Toggle active
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByText('User Updated')).toBeVisible();
    await expect(page.getByRole('dialog')).toBeHidden();

    // Delete User
    await page.locator('.p-datatable-tbody button').filter({ has: page.locator('.pi-trash') }).first().click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('Are you sure you want to delete')).toBeVisible();
    
    await page.getByRole('button', { name: 'Yes' }).click();
    
    // Wait for success toast (Users.vue doesn't seem to have a toast for delete success in the snippet I read? 
    // Let me check Users.vue again.
    // Ah, I didn't read the deleteUser function in Users.vue. Let's assume it has one or check if the row disappears.
    // But usually there is a toast.
    
    // Verify User Deleted
    await expect(page.getByText(testEmail)).toBeHidden();
  });
});
