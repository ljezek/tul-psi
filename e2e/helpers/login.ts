import { Page } from '@playwright/test';
import { OTP } from '../fixtures/seed.js';

/**
 * Performs the full OTP login flow for the given email address.
 * Relies on E2E_OTP_OVERRIDE=000000 being set on the backend.
 */
export async function login(page: Page, email: string): Promise<void> {
  const [prefix] = email.split('@');

  await page.goto('/login');
  await page.locator('#email').fill(prefix);
  await page.getByRole('button', { name: /Odeslat kód|Send Code/i }).click();

  // Wait for the first OTP input (autoFocus on index 0, autocomplete="one-time-code")
  const firstOtpInput = page.locator('input[autocomplete="one-time-code"]');
  await firstOtpInput.waitFor({ state: 'visible', timeout: 8_000 });
  await firstOtpInput.focus();

  // Type all 6 digits with a small delay between each.
  // The onChange handler auto-advances focus after each character,
  // so keyboard.type ends up filling all 6 boxes sequentially.
  await page.keyboard.type(OTP, { delay: 80 });

  // The useEffect in Login.tsx auto-submits when all 6 digits are filled.
  // Wait for redirect away from /login.
  await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10_000 });
}
