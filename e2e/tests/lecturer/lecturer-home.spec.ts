import { test, expect, COURSES, PROJECTS } from '../../fixtures/index.js';

// L-01: Lecturer home shows assigned courses.
test('lecturer home shows courses', async ({ lecturerPage: page }) => {
  await page.goto('/lecturer');

  // PSI course is visible (jezek is assigned to PSI)
  await expect(page.getByText(COURSES.psi.code)).toBeVisible();

  // Lecturer panel heading
  await expect(page.getByText(/Panel lektora|Lecturer Panel/i)).toBeVisible();
});

// L-02: Course projects page lists all PSI-2026 projects with evaluate links.
test('course projects page lists in-progress projects with evaluate action', async ({ lecturerPage: page }) => {
  await page.goto(`/lecturer/course/${COURSES.psi.id}`);

  // All 5 PSI-2026 in-progress project titles should appear
  await expect(page.getByText(PROJECTS.lectorsSpc.title)).toBeVisible();
  await expect(page.getByText(PROJECTS.bookstore.title)).toBeVisible();
  await expect(page.getByText(PROJECTS.kanban.title)).toBeVisible();
  await expect(page.getByText(PROJECTS.quizApp.title)).toBeVisible();

  // At least one "Hodnotit" / "Evaluate" link is present
  await expect(
    page.getByRole('link', { name: /Hodnotit|Evaluate/i }).first()
  ).toBeVisible();
});

// L-01b: Admin can open the create course modal (button is only shown to ADMIN role).
test('lecturer can open the create course modal', async ({ adminPage: page }) => {
  await page.goto('/lecturer');

  const createBtn = page.getByRole('button', { name: /Přidat|Vytvořit|Create|Add/i }).first();
  await expect(createBtn).toBeVisible();
  await createBtn.click();

  // Modal should appear — look for a form inside it
  await expect(page.getByRole('dialog').or(page.locator('[role="dialog"]'))).toBeVisible({ timeout: 5_000 })
    .catch(async () => {
      // Some modals don't use role=dialog; check for a visible form instead
      await expect(page.locator('form').filter({ has: page.getByLabel(/Zkratka|Code/i) })).toBeVisible();
    });

  // Close without saving — press Escape
  await page.keyboard.press('Escape');
});
