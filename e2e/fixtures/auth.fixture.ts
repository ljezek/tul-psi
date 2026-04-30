import { test as base, Browser, Page } from '@playwright/test';
import { login } from '../helpers/login.js';
import { USERS } from './seed.js';

type AuthFixtures = {
  /** Page logged in as PSI Admin */
  adminPage: Page;
  /** Page logged in as Lukáš Ježek (PSI lecturer) */
  lecturerPage: Page;
  /** Page logged in as Jan Novák (member of project 4) */
  studentPage: Page;
  /** Page logged in as Alice Nováková (project 1 — results unlocked) */
  studentAlicePage: Page;
};

function makeAuthPage(email: string) {
  return async ({ browser }: { browser: Browser }, use: (page: Page) => Promise<void>) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    await login(page, email);
    await use(page);
    await context.close();
  };
}

export const test = base.extend<AuthFixtures>({
  adminPage:       makeAuthPage(USERS.admin.email),
  lecturerPage:    makeAuthPage(USERS.jezek.email),
  studentPage:     makeAuthPage(USERS.jan.email),
  studentAlicePage: makeAuthPage(USERS.alice.email),
});

export { expect } from '@playwright/test';
