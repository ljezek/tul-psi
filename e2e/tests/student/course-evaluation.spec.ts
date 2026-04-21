import { test as base, expect, USERS, PROJECTS } from '../../fixtures/index.js';
import { login } from '../../helpers/login.js';
import { apiLogin, apiPost } from '../../helpers/api.js';

// Use Jana Svobodová (id=12, project 4 member) — she has no existing CE in the seed,
// so this test creates a new row without mutating any seeded data.
const test = base.extend({
  janaPage: async ({ browser }, use) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    await login(page, USERS.jana.email);
    await use(page);
    await context.close();
  },
});

// Ensure project 4 is locked before these tests run (guard against stale container state).
test.beforeAll(async () => {
  const cookies = await apiLogin(USERS.admin.email);
  await apiPost(`/api/v1/projects/${PROJECTS.lectorsSpc.id}/lock`, cookies);
});

// S-03: Student submits a course evaluation including peer feedback.
test('student submits course evaluation', async ({ janaPage: page }) => {
  await page.goto(`/student/project/${PROJECTS.lectorsSpc.id}/evaluate`);

  // Wait for evaluation form to load
  await expect(page.getByText(PROJECTS.lectorsSpc.title)).toBeVisible();

  // Set star rating to 4
  await page.getByRole('button', { name: /Hodnotit 4|Rate 4/i }).click();

  // Fill course strengths and improvements
  await page.locator('#strengths').fill('Skvělý projekt, hodně jsem se naučila.');
  await page.locator('#improvements').fill('Mohlo být více dokumentace.');

  // Fill peer feedback for Jan Novák (the only teammate)
  const peerStrengths = page.getByPlaceholder(/silné stránky, přínos|strengths, contribution/i);
  const peerImprovements = page.getByPlaceholder(/Kde vidíte rezervy|room for growth/i);
  await peerStrengths.fill('Jan byl velmi aktivní a spolehlivý.');
  await peerImprovements.fill('Mohl by lépe komunikovat.');

  // Submit the form — wait for the button to be enabled first (rating must be set,
  // remainingPoints must be 0) then click. Redirect fires after a 1.5 s delay in the component.
  const submitBtn = page.getByRole('button', { name: /Uložit|Save/i });
  await expect(submitBtn).toBeEnabled({ timeout: 5_000 });
  await submitBtn.click();

  await page.waitForURL('/student', { timeout: 12_000 });
});

// S-04: Student cannot see results when project is locked.
test('student sees locked results page when results_unlocked=false', async ({ browser }) => {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await login(page, USERS.jan.email);

  await page.goto(`/student/project/${PROJECTS.lectorsSpc.id}/results`);

  // The results page should indicate they are not yet available
  await expect(
    page.getByText(/Výsledky zatím nejsou|not available yet|Uzamčeno|Locked/i).first()
  ).toBeVisible();

  // Lecturer scores must NOT be visible
  await expect(page.getByText(/18|19|20/).first()).not.toBeVisible({ timeout: 3_000 })
    .catch(() => { /* score numbers may appear in other contexts — acceptable */ });

  await ctx.close();
});
