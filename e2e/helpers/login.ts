import { Page } from '@playwright/test';
import { OTP } from '../fixtures/seed.js';

const LOGIN_MAX_ATTEMPTS = 4;
const OTP_INPUT_TIMEOUT_MS = 35_000;
const LOGIN_REDIRECT_TIMEOUT_MS = 20_000;
const LOGIN_RETRY_DELAY_MS = 12_000;

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Performs the full OTP login flow for the given email address.
 * Relies on E2E_OTP_OVERRIDE=000000 being set on the backend.
 */
export async function login(page: Page, email: string): Promise<void> {
  const [prefix] = email.split('@');
  let lastError = 'unknown login failure';

  for (let attempt = 1; attempt <= LOGIN_MAX_ATTEMPTS; attempt += 1) {
    try {
      await page.goto('/login');
      await page.locator('#email').fill(prefix);
      await page.getByRole('button', { name: /Odeslat kód|Send Code/i }).click();

      // Wait for OTP step. This can take longer in CI when the backend is busy
      // or request-otp is temporarily rate-limited.
      const firstOtpInput = page.locator('input[autocomplete="one-time-code"]');
      await firstOtpInput.waitFor({ state: 'visible', timeout: OTP_INPUT_TIMEOUT_MS });
      await firstOtpInput.focus();

      // The onChange handler auto-advances focus, so typing fills all 6 boxes.
      await page.keyboard.type(OTP, { delay: 80 });

      // Auto-submit is triggered when all digits are entered.
      await page.waitForURL(url => !url.pathname.includes('/login'), {
        timeout: LOGIN_REDIRECT_TIMEOUT_MS,
      });
      return;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
      if (attempt < LOGIN_MAX_ATTEMPTS) {
        await sleep(LOGIN_RETRY_DELAY_MS);
        continue;
      }
    }
  }

  throw new Error(
    `login failed for ${email} after ${LOGIN_MAX_ATTEMPTS} attempts: ${lastError}`
  );
}
