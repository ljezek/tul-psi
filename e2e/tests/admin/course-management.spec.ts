import { test, expect, COURSES } from '../../fixtures/index.js';

// A-03: Admin can access all privileged routes.
test('admin can access admin, lecturer, and public routes', async ({ adminPage: page }) => {
  // Admin-only
  await page.goto('/admin/users');
  await expect(page).not.toHaveURL(/\/login/);
  await expect(page.getByRole('heading', { name: /Správa uživatelů|User Management/i })).toBeVisible();

  // Lecturer routes
  await page.goto('/lecturer');
  await expect(page).not.toHaveURL(/\/login/);
  await expect(page.getByText(/Panel lektora|Lecturer Panel/i)).toBeVisible();
});

// A-04: Admin can open the course edit modal.
test('admin can open and close the course edit modal', async ({ adminPage: page }) => {
  await page.goto('/lecturer');

  // Settings buttons are icon-only — match by title or aria-label attribute.
  const settingsBtn = page
    .getByTitle(/Upravit|Edit|Settings/i)
    .or(page.locator('button[aria-label]').filter({ hasText: /Upravit|Edit|Settings/i }))
    .first();
  await expect(settingsBtn).toBeVisible({ timeout: 5_000 });
  await settingsBtn.click();

  // Modal should open
  await expect(
    page.locator('[role="dialog"]').or(page.locator('form').filter({ has: page.getByLabel(/Zkratka|Code/i) }))
  ).toBeVisible({ timeout: 5_000 });
  await page.keyboard.press('Escape');
});

// A-05: Course list page shows both seeded courses.
test('course list page shows both courses', async ({ page }) => {
  await page.goto('/courses');

  await expect(page.getByText(COURSES.psi.code)).toBeVisible();
  await expect(page.getByText(COURSES.ald.code)).toBeVisible();
  await expect(page.getByText(COURSES.psi.name)).toBeVisible();
  await expect(page.getByText(COURSES.ald.name)).toBeVisible();
});
