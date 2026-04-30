import { test, expect, USERS, PROJECTS } from '../../fixtures/index.js';

// S-05: Student can view results on a project where results are unlocked.
// Alice (id=5) is a member of project 1 (TUL Event Planner, results_unlocked=true).
test('student sees evaluation results when results are unlocked', async ({ studentAlicePage: page }) => {
  await page.goto(`/student/project/${PROJECTS.eventPlanner.id}/results`);

  // Results page heading
  await expect(page.getByText(/Výsledky hodnocení|Evaluation Results/i)).toBeVisible();

  // Seeded scores for project 1: Ježek gave 18+19+17=54, Špánek gave 17+20+16=53
  // Check for lecturer evaluation section heading (scores are inside it)
  await expect(page.getByText(/Hodnocení lektora|Hodnocení lektorů|Lecturer Evaluation/i).first()).toBeVisible();

  // Peer bonus section — Alice received 10 pts from Bob (CE id=2, peer_feedback)
  await expect(page.getByText(/Týmové hodnocení|Team Evaluation|Peer/i)).toBeVisible();

  // Pass/fail verdict
  await expect(page.getByText(/SPLNĚNO|PASS|NESPLNĚNO|FAIL/i)).toBeVisible();
});

// S-05b: Results page is accessible via the student home link.
test('student can navigate from student home to results', async ({ studentAlicePage: page }) => {
  // Alice's project 1 has results unlocked; there should be a "Zobrazit výsledky" link
  await page.goto('/student');

  // Find the results link for project 1
  const resultsLink = page.getByRole('link', { name: /Zobrazit výsledky|View Results/i }).first();
  await expect(resultsLink).toBeVisible();
  await resultsLink.click();

  await expect(page.getByText(/Výsledky hodnocení|Evaluation Results/i)).toBeVisible();
});
