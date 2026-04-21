import { test, expect, USERS } from '../../fixtures/index.js';
import { apiLogin, apiPatch } from '../../helpers/api.js';

// Ensure Dan starts active before A-02 runs (stale container may have left him inactive).
test.beforeAll(async () => {
  const cookies = await apiLogin(USERS.admin.email);
  await apiPatch(`/api/v1/users/${USERS.dan_k.id}`, { is_active: true }, cookies);
});

// A-01: Admin creates a new student user.
// Idempotent: if the user already exists (stale container), the test verifies it's visible.
test('admin creates a new student user', async ({ adminPage: page }) => {
  await page.goto('/admin/users');

  // Wait for user list to load
  await expect(page.getByText(USERS.admin.name)).toBeVisible();

  // If user already exists from a previous run, skip creation
  const alreadyExists = await page.getByText('Test E2E Student').isVisible();
  if (!alreadyExists) {
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

    // Submit — scope to dialog to avoid clicking the "Přidat uživatele" opener button
    await page.getByRole('dialog').getByRole('button', { name: /Přidat|Add/i }).click();
  }

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

  // Find the active/inactive toggle — it's a custom sr-only checkbox with id="user-status"
  const activeToggle = page.locator('#user-status');

  // The toggle should currently be checked (user is active)
  await expect(activeToggle).toBeChecked();

  // Deactivate — click the label because the sr-only div intercepts pointer events
  await page.locator('label:has(#user-status)').click();
  await expect(activeToggle).not.toBeChecked();

  // Save and wait for modal to close before interacting with the toolbar
  await page.getByRole('dialog').getByRole('button', { name: /Uložit|Save/i }).click();
  await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 5_000 });

  // After deactivation Dan is filtered out (showInactive=false by default).
  // Enable the "show inactive" toolbar toggle so his row reappears.
  await page.locator('label').filter({ hasText: /Neaktivní|Inactive/i }).click();
  await page.getByText(USERS.dan_k.name).waitFor({ state: 'visible', timeout: 5_000 });

  // Re-open the user edit modal and reactivate
  await danRow.getByRole('button', { name: /Upravit|Edit/i }).click();

  const toggle2 = page.locator('#user-status');
  await page.locator('label:has(#user-status)').click();
  await expect(toggle2).toBeChecked();

  // Save restored state
  await page.getByRole('dialog').getByRole('button', { name: /Uložit|Save/i }).click();

  // User should still appear (active) in the default view (showInactive=false by default)
  await expect(page.getByText(USERS.dan_k.name)).toBeVisible({ timeout: 8_000 });
});
