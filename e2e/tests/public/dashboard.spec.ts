import { test, expect, PROJECTS, COURSES } from '../../fixtures/index.js';

// P-01: Dashboard loads and project filtering by course works.
test('dashboard shows projects and course filter works', async ({ page }) => {
  await page.goto('/');

  // At least one seeded project title is visible
  await expect(page.getByText(PROJECTS.eventPlanner.title)).toBeVisible();

  // Select PSI course filter — the select contains course codes or names
  const courseSelect = page.locator('select').filter({ hasText: /Předmět|Subject|Všechny|All/ }).first();
  if (await courseSelect.count() > 0) {
    await courseSelect.selectOption({ value: COURSES.psi.code }); // value="PSI", label="PSI - Pokročilé..."
  } else {
    // Fallback: look for a button/chip filter
    await page.getByRole('button', { name: new RegExp(COURSES.psi.code, 'i') }).click();
  }

  // After filtering for PSI, ALD projects should not be visible
  await expect(page.getByText('Analýza výkonnosti distribuovaných systémů')).not.toBeVisible();

  // PSI projects remain visible
  await expect(page.getByText(PROJECTS.eventPlanner.title)).toBeVisible();
});

// P-01b: Search filter narrows results by project title.
test('search filter narrows project list', async ({ page }) => {
  await page.goto('/');

  const searchInput = page.getByPlaceholder(/Hledat|Search/i);
  await searchInput.fill('QuizApp');

  await expect(page.getByText('QuizApp').first()).toBeVisible();
  // Other projects should be hidden
  await expect(page.getByText(PROJECTS.eventPlanner.title)).not.toBeVisible();
});
