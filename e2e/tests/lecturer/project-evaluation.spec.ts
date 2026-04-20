import { test, expect, PROJECTS } from '../../fixtures/index.js';

// L-03: Lecturer saves a draft evaluation then submits it.
// Uses project 7 (PSI - Kanban Board) — no existing project_evaluation in the seed.
// The ephemeral container means no cleanup is needed; the inserted row is discarded on teardown.
test('lecturer saves draft and submits project evaluation', async ({ lecturerPage: page }) => {
  await page.goto(`/lecturer/project/${PROJECTS.kanban.id}/evaluate`);

  // Wait for evaluation form to load
  await expect(page.getByText(PROJECTS.kanban.title)).toBeVisible();

  // PSI has 3 criteria (funkcionalita, code_quality, nfr) — each with a range slider.
  // Set all sliders to max (20) by filling the range inputs.
  const sliders = page.locator('input[type="range"]');
  const sliderCount = await sliders.count();
  for (let i = 0; i < sliderCount; i++) {
    const slider = sliders.nth(i);
    const max = await slider.getAttribute('max') ?? '20';
    await slider.fill(max);
  }

  // Fill all strengths textareas (aria-label contains criterion description)
  const strengthsAreas = page.getByPlaceholder(/Popište silné stránky|Describe the strengths/i);
  const strengthsCount = await strengthsAreas.count();
  for (let i = 0; i < strengthsCount; i++) {
    await strengthsAreas.nth(i).fill('Výborná práce na tomto kritériu.');
  }

  // Fill all improvements textareas
  const improvementsAreas = page.getByPlaceholder(/Kde vidíte prostor|Where do you see room/i);
  const improvementsCount = await improvementsAreas.count();
  for (let i = 0; i < improvementsCount; i++) {
    await improvementsAreas.nth(i).fill('Vše je v pořádku, drobné rezervy.');
  }

  // Save as draft first
  await page.getByRole('button', { name: /Uložit koncept|Save Draft/i }).click();

  // Reload to verify persistence
  await page.reload();
  await expect(page.getByText(PROJECTS.kanban.title)).toBeVisible();

  // After reload, strengths should still contain the filled text
  const firstStrengths = page.getByPlaceholder(/Popište silné stránky|Describe the strengths/i).first();
  await expect(firstStrengths).toHaveValue('Výborná práce na tomto kritériu.');

  // Submit final evaluation
  await page.getByRole('button', { name: /Odevzdat hodnocení|Submit Evaluation/i }).click();

  // Should navigate to the course projects page after submit
  await page.waitForURL(url => url.pathname.includes(`/lecturer/course/`), { timeout: 10_000 });
});
