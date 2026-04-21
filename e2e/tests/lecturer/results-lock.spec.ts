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

  // Scope all actions to the Kanban project card
  const kanbanCard = page.locator('div').filter({ has: page.locator('h3, h2').filter({ hasText: PROJECTS.kanban.title }) }).last();

  // Find the unlock button scoped to the Kanban card
  const unlockBtn = kanbanCard.getByRole('button', { name: /Odemknout výsledky|Unlock Results/i });
  await expect(unlockBtn).toBeVisible();
  await unlockBtn.click();

  // After unlock, "Výsledky odemčeny" badge should appear on the Kanban card
  await expect(kanbanCard.getByText(/Výsledky odemčeny|Results Unlocked/i)).toBeVisible({ timeout: 8_000 });

  // Re-lock: the relock button is admin-only and appears after unlock
  const relockBtn = kanbanCard.getByRole('button', { name: /Uzamknout|Relock|lock/i });
  await expect(relockBtn).toBeVisible({ timeout: 5_000 });
  await relockBtn.click();

  // After relock, the "Výsledky odemčeny" badge should disappear from the Kanban card
  await expect(kanbanCard.getByText(/Výsledky odemčeny|Results Unlocked/i)).not.toBeVisible({ timeout: 8_000 });
  // Unlock button should reappear
  await expect(kanbanCard.getByRole('button', { name: /Odemknout výsledky|Unlock Results/i })).toBeVisible();
});

// L-03b: Lecturer can view the results page for a completed project.
test('lecturer can view unlocked project results', async ({ lecturerPage: page }) => {
  await page.goto(`/lecturer/project/${PROJECTS.eventPlanner.id}/results`);

  // Scores and peer feedback should be visible
  await expect(page.getByText(/Hodnocení lektora|Hodnocení lektorů|Lecturer Evaluation/i).first()).toBeVisible();
  await expect(page.getByText(/Studentská zpětná vazba|Peer Feedback/i)).toBeVisible();
});
