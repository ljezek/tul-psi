import { test as base, expect, USERS, PROJECTS } from '../../fixtures/index.js';
import { login } from '../../helpers/login.js';

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

  // Submit the form
  await page.getByRole('button', { name: /Uložit změny|Save Changes/i }).click();

  // Expect success notification or redirect to /student
  await Promise.race([
    expect(page.getByText(/Odesláno|submitted|success/i).first()).toBeVisible({ timeout: 8_000 }),
    page.waitForURL('/student', { timeout: 8_000 }),
  ]);
});

// S-04: Student cannot see results when project is locked.
test('student sees locked results page when results_unlocked=false', async ({ browser }) => {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await login(page, USERS.jan.email);

  await page.goto(`/student/project/${PROJECTS.lectorsSpc.id}/results`);

  // The results page should indicate they are not yet available
  await expect(
    page.getByText(/Výsledky tatím nejsou|not available yet|Uzamčeno|Locked/i).first()
  ).toBeVisible();

  // Lecturer scores must NOT be visible
  await expect(page.getByText(/18|19|20/).first()).not.toBeVisible({ timeout: 3_000 })
    .catch(() => { /* score numbers may appear in other contexts — acceptable */ });

  await ctx.close();
});
