import { chromium } from '@playwright/test';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8001';
const FRONTEND_URL = process.env.FRONTEND_URL ?? 'http://localhost:3000';
const MAX_RETRIES = 30;
const RETRY_DELAY_MS = 2_000;

async function waitForUrl(url: string, label: string): Promise<void> {
  for (let i = 0; i < MAX_RETRIES; i++) {
    try {
      const res = await fetch(url);
      if (res.ok) {
        console.log(`[global-setup] ${label} is ready.`);
        return;
      }
    } catch {
      // not yet ready
    }
    console.log(`[global-setup] Waiting for ${label}… (${i + 1}/${MAX_RETRIES})`);
    await new Promise(r => setTimeout(r, RETRY_DELAY_MS));
  }
  throw new Error(`[global-setup] ${label} at ${url} did not become ready in time.`);
}

export default async function globalSetup() {
  await waitForUrl(`${BACKEND_URL}/health`, 'Backend');
  await waitForUrl(FRONTEND_URL, 'Frontend');

  // Warm up one browser context so the first test does not pay cold-start cost.
  const browser = await chromium.launch();
  await browser.close();
}
