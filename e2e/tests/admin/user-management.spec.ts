import { test, expect, USERS } from '../../fixtures/index.js';

// A-01: Admin creates a new student user.
// The new user row is inserted into the ephemeral container — no cleanup needed.
test('admin creates a new student user', async ({ adminPage: page }) => {
  await page.goto('/admin/users');

  // Wait for user list to load
  await expect(page.getByText(USERS.admin.name)).toBeVisible();

  // Open create user modal
  await page.getByRole('button', { name: /Přidat uživatele|Add User|UserPlus/i }).click();

  // Fill name — email auto-generates from name
  const nameInput = page.getByLabel(/Jméno|Name/i).first();
  await nameInput.fill('Test E2E Student');

  // Select STUDENT role (it may be the default, but explicitly set it)
  const roleSelect = page.getByRole('combobox', { name: /Role/i }).or(
    page.locator('select').filter({ has: page.getByText(/STUDENT|Student/i) })
  ).first();
  if (await roleSelect.count() > 0) {
    await roleSelect.selectOption({ value: 'STUDENT' });
  }

  // Submit
  await page.getByRole('button', { name: /Uložit|Save/i }).last().click();

  // New user should appear in the table
  await expect(page.getByText('Test E2E Student')).toBeVisible({ timeout: 8_000 });
});

// A-02: Admin can deactivate and reactivate a user.
// Uses dan.kerslager (id=25) — a safe test target with no critical data dependencies.
test('admin deactivates and reactivates a user', async ({ adminPage: page }) => {
  await page.goto('/admin/users');

  // Locate Dan Keršláger's row
  await expect(page.getByText(USERS.dan_k.name)).toBeVisible();

  // Click edit on Dan's row
  const danRow = page.locator('tr, [data-testid]').filter({ hasText: USERS.dan_k.name });
  await danRow.getByRole('button', { name: /Upravit|Edit/i }).click();

  // Find the active/inactive toggle
  const activeToggle = page.getByRole('checkbox', { name: /Aktivní|Active/i })
    .or(page.locator('input[type="checkbox"]').filter({ hasText: /Aktivní|Active/i }))
    .first();

  // The toggle should currently be checked (user is active)
  await expect(activeToggle).toBeChecked();

  // Deactivate
  await activeToggle.click();
  await expect(activeToggle).not.toBeChecked();

  // Save
  await page.getByRole('button', { name: /Uložit|Save/i }).last().click();

  // Re-open the user and reactivate
  await page.getByText(USERS.dan_k.name).waitFor({ timeout: 5_000 });
  await danRow.getByRole('button', { name: /Upravit|Edit/i }).click();

  const toggle2 = page.getByRole('checkbox', { name: /Aktivní|Active/i }).first();
  await toggle2.click();
  await expect(toggle2).toBeChecked();

  // Save restored state
  await page.getByRole('button', { name: /Uložit|Save/i }).last().click();

  // User should still appear (active) in the default view (showInactive=false by default)
  await expect(page.getByText(USERS.dan_k.name)).toBeVisible({ timeout: 8_000 });
});
