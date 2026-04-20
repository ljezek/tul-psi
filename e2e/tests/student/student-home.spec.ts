import { test, expect, USERS, PROJECTS } from '../../fixtures/index.js';
import { login } from '../../helpers/login.js';

// S-01: Full OTP login flow for a student.
test('student OTP login redirects to home and shows profile name', async ({ page }) => {
  await login(page, USERS.jan.email);

  // Must land somewhere other than /login
  expect(page.url()).not.toContain('/login');

  // Profile dropdown or header shows the user's name
  await expect(page.getByText(USERS.jan.name)).toBeVisible();
});

// S-02: Student home shows only projects where the student is a member.
test('student home shows only own projects', async ({ studentPage: page }) => {
  await page.goto('/student');

  // Jan Novák is a member of project 4 only (PSI-2026)
  await expect(page.getByText(PROJECTS.lectorsSpc.title)).toBeVisible();

  // Jan is NOT a member of project 7 (Kanban Board) or QuizApp
  await expect(page.getByText(PROJECTS.kanban.title)).not.toBeVisible();
  await expect(page.getByText(PROJECTS.quizApp.title)).not.toBeVisible();
});

// S-02b: Member email addresses ARE visible to authenticated members.
test('member emails are visible when authenticated as a member', async ({ studentPage: page }) => {
  await page.goto(`/projects/${PROJECTS.lectorsSpc.id}`);

  // jan.novak is a member — his own email or teammate's email should now be shown
  await expect(page.getByText(USERS.jana.email)).toBeVisible();
});
