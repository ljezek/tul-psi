import { test, expect } from '../../fixtures/index.js';

// AC-01: Unauthenticated users are redirected to /login for all protected routes.
test('unauthenticated users are redirected to /login', async ({ page }) => {
  const protectedRoutes = ['/profile', '/student', '/lecturer', '/admin/users'];

  for (const route of protectedRoutes) {
    await page.goto(route);
    await expect(page).toHaveURL(/\/login/, { timeout: 8_000 });
  }
});

// AC-02: Students cannot access lecturer or admin routes.
test('student is redirected from lecturer and admin routes', async ({ studentPage: page }) => {
  // Lecturer route
  await page.goto('/lecturer');
  await expect(page).not.toHaveURL(/\/lecturer/, { timeout: 8_000 });
  // Should land on / (root redirect)
  await expect(page).toHaveURL('/', { timeout: 5_000 });

  // Admin route
  await page.goto('/admin/users');
  await expect(page).not.toHaveURL(/\/admin/, { timeout: 8_000 });
  await expect(page).toHaveURL('/', { timeout: 5_000 });
});

// AC-03: Lecturers cannot access admin or student routes.
test('lecturer is redirected from admin and student routes', async ({ lecturerPage: page }) => {
  await page.goto('/admin/users');
  await expect(page).not.toHaveURL(/\/admin/, { timeout: 8_000 });
  await expect(page).toHaveURL('/', { timeout: 5_000 });

  await page.goto('/student');
  await expect(page).not.toHaveURL(/\/student/, { timeout: 8_000 });
  await expect(page).toHaveURL('/', { timeout: 5_000 });
});

// AC-04: Student cannot access another project's evaluation form if not a member.
// jan.novak (id=11) is member of project 4, not project 7.
test('student cannot evaluate a project they are not a member of', async ({ studentPage: page }) => {
  // Navigate directly to project 7's evaluation page
  await page.goto('/student/project/7/evaluate');

  // The API will return 403/404; the page should show an error state (not an empty form)
  await expect(
    page.getByText(/error|chyba|nenalezen|not found|403|přístup/i).first()
  ).toBeVisible({ timeout: 8_000 });
});

// AC-05: Public routes remain accessible after authentication.
test('authenticated student can still view public project pages', async ({ studentPage: page }) => {
  await page.goto('/');
  // Dashboard loads normally
  await expect(page.getByText(/Prohlížeč projektů|Project Browser/i)).toBeVisible();

  await page.goto('/courses');
  await expect(page.getByText(/Seznam předmětů|Course List/i)).toBeVisible();
});
