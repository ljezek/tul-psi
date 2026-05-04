import { test, expect, PROJECTS, USERS } from '../../fixtures/index.js';

// P-02: Project detail page is accessible without authentication.
test('project detail is publicly accessible', async ({ page }) => {
  await page.goto(`/projects/${PROJECTS.lectorsSpc.id}`);

  await expect(page.getByText(PROJECTS.lectorsSpc.title)).toBeVisible();

  // GitHub link renders
  await expect(page.getByRole('link', { name: /GitHub|Repo|repo|Zdrojový kód|Source Code/i }).first()).toBeVisible();

  // Technology chips include known entries for project 4
  await expect(page.getByText('React', { exact: true })).toBeVisible();
  await expect(page.getByText('FastAPI', { exact: true })).toBeVisible();
});

// P-03: Member email addresses are NOT shown to unauthenticated visitors.
test('member emails are hidden from unauthenticated users', async ({ page }) => {
  await page.goto(`/projects/${PROJECTS.lectorsSpc.id}`);

  // Wait for the page to finish loading
  await expect(page.getByText(PROJECTS.lectorsSpc.title)).toBeVisible();

  // jan.novak and jana.svobodova are members — their emails must not be visible
  await expect(page.getByText(USERS.jan.email)).not.toBeVisible();
  await expect(page.getByText(USERS.jana.email)).not.toBeVisible();
});

// P-03b: Completed project detail with unlocked results renders for public (no scores shown).
test('public cannot see evaluation scores on unlocked project', async ({ page }) => {
  await page.goto(`/projects/${PROJECTS.eventPlanner.id}`);

  await expect(page.getByText(PROJECTS.eventPlanner.title)).toBeVisible();

  // Scores section is auth-gated — not visible without login
  await expect(page.getByText(/Hodnocení lektorů|Lecturer Evaluations/i)).not.toBeVisible();
});
