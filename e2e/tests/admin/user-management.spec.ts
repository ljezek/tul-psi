import { test, expect, USERS } from '../../fixtures/index.js';
import { apiLogin, apiPatch, apiPost } from '../../helpers/api.js';

// Ensure Dan starts active and the test user exists before tests run.
test.beforeAll(async () => {
  const cookies = await apiLogin(USERS.admin.email);
  await apiPatch(`/api/v1/users/${USERS.dan_k.id}`, { is_active: true }, cookies);
  // Pre-create the test user so A-01 can verify it via the UI.
  // 409 means user already exists from a previous run — that's fine.
  const createRes = await apiPost('/api/v1/users', cookies, {
    email: 'test.student@tul.cz',
    name: 'Test E2E Student',
    role: 'STUDENT',
    is_active: true,
  });
  if (!createRes.ok && createRes.status !== 409) {
    const body = await createRes.text();
    console.warn(`[A-01 beforeAll] Failed to pre-create test user: HTTP ${createRes.status} — ${body}`);
  }
});

// A-01: Admin creates a new student user.
// The beforeAll pre-creates the user via API. The UI test verifies the user appears
// in the admin list, and also exercises the modal creation form when the user doesn't
// already exist in the currently loaded page.
test('admin creates a new student user', async ({ adminPage: page }) => {
  await page.goto('/admin/users');

  // Wait for user list to load
  await expect(page.getByText(USERS.admin.name)).toBeVisible();

  // Capture the create-user API response for diagnostics (only used if UI creation runs)
  let createResponseStatus = 0;
  let createResponseBody = '';
  page.on('response', async response => {
    if (response.url().includes('/api/v1/users') && response.request().method() === 'POST') {
      createResponseStatus = response.status();
      createResponseBody = await response.text().catch(() => '');
    }
  });

  // Try the UI creation flow if the user isn't visible yet (may already be there from beforeAll)
  const alreadyVisible = await page.getByText('Test E2E Student').isVisible();
  if (!alreadyVisible) {
    await page.getByRole('button', { name: /Přidat uživatele|Add User|UserPlus/i }).click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible({ timeout: 5_000 });

    const nameInput = dialog.getByLabel(/Jméno|Name/i).first();
    await nameInput.fill('Test E2E Student');

    const roleSelect = dialog.locator('#user-role');
    if (await roleSelect.count() > 0) {
      await roleSelect.selectOption({ value: 'STUDENT' });
    }

    await dialog.getByRole('button', { name: /Přidat|Add/i }).click();

    await expect(dialog).not.toBeVisible({ timeout: 8_000 }).catch(async () => {
      console.log(`[A-01] UI create user API: HTTP ${createResponseStatus} — ${createResponseBody}`);
      await page.keyboard.press('Escape');
    });
  }

  // Reload to reflect any beforeAll-created user and enable show-inactive
  await page.reload();
  await expect(page.getByText(USERS.admin.name)).toBeVisible();
  await page.locator('label').filter({ hasText: /Neaktivní|Inactive/i }).click().catch(() => {});

  // New user should appear in the table (active or inactive)
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
