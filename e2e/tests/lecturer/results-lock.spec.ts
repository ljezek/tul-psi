import { test, expect, PROJECTS, COURSES } from '../../fixtures/index.js';

// L-04: Admin can unlock and re-lock results on a project.
// Uses project 7 (Kanban Board, results_unlocked=false in seed).
// Test performs two toggles: false→true→false, leaving DB in seed state.
// Note: only ADMIN can re-lock; lecturer can only unlock.
test('admin can unlock and re-lock project results', async ({ adminPage: page }) => {
  // Accept any window.confirm dialogs automatically
  page.on('dialog', dialog => dialog.accept());

  await page.goto(`/lecturer/course/${COURSES.psi.id}`);

  // Verify project 7 is listed and currently locked (no "Výsledky odemčeny" badge)
  await expect(page.getByText(PROJECTS.kanban.title)).toBeVisible();

  // Find the unlock button for project 7
  // The button triggers window.confirm then calls POST /projects/{id}/unlock
  const unlockBtn = page.getByRole('button', { name: /Odemknout výsledky|Unlock Results/i }).first();
  await expect(unlockBtn).toBeVisible();
  await unlockBtn.click();

  // After unlock, "Výsledky odemčeny" badge should appear on that project
  await expect(page.getByText(/Výsledky odemčeny|Results Unlocked/i)).toBeVisible({ timeout: 8_000 });

  // Re-lock: the relock button is admin-only and appears after unlock
  const relockBtn = page.getByRole('button', { name: /Uzamknout|Relock|lock/i }).first();
  await expect(relockBtn).toBeVisible({ timeout: 5_000 });
  await relockBtn.click();

  // After relock, the "Výsledky odemčeny" badge should disappear
  await expect(page.getByText(/Výsledky odemčeny|Results Unlocked/i)).not.toBeVisible({ timeout: 8_000 });
  // Unlock button should reappear
  await expect(page.getByRole('button', { name: /Odemknout výsledky|Unlock Results/i }).first()).toBeVisible();
});

// L-03b: Lecturer can view the results page for a completed project.
test('lecturer can view unlocked project results', async ({ lecturerPage: page }) => {
  await page.goto(`/lecturer/project/${PROJECTS.eventPlanner.id}/results`);

  // Scores and peer feedback should be visible
  await expect(page.getByText(/Hodnocení lektorů|Lecturer Evaluations/i)).toBeVisible();
  await expect(page.getByText(/Studentská zpětná vazba|Peer Feedback/i)).toBeVisible();
});
