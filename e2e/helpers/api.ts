/**
 * Thin wrappers around direct backend API calls.
 * Used in afterAll hooks to restore seeded state after mutating tests.
 */

import { OTP } from '../fixtures/seed.js';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8001';
const API_LOGIN_MAX_ATTEMPTS = 6;
const API_LOGIN_RETRY_DELAY_MS = 12_000;

interface SessionCookies {
  session: string;
  xsrf: string;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function responseBodySafe(response: Response): Promise<string> {
  try {
    return await response.text();
  } catch {
    return '';
  }
}

/** Log in via the API (not the browser) and return raw session cookies. */
export async function apiLogin(email: string): Promise<SessionCookies> {
  let lastFailure = 'unknown error';

  for (let attempt = 1; attempt <= API_LOGIN_MAX_ATTEMPTS; attempt += 1) {
    // Step 1: request OTP
    const requestRes = await fetch(`${BACKEND_URL}/api/v1/auth/otp/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    if (requestRes.status === 429) {
      lastFailure = `OTP request rate-limited (429) on attempt ${attempt}`;
      if (attempt < API_LOGIN_MAX_ATTEMPTS) {
        await sleep(API_LOGIN_RETRY_DELAY_MS);
        continue;
      }
    } else if (!requestRes.ok) {
      const body = await responseBodySafe(requestRes);
      throw new Error(`apiLogin OTP request failed for ${email}: ${requestRes.status} ${body}`);
    }

    // Step 2: verify OTP (E2E_OTP_OVERRIDE=000000)
    const verifyRes = await fetch(`${BACKEND_URL}/api/v1/auth/otp/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp: OTP }),
    });

    if (verifyRes.status === 429 || verifyRes.status === 401) {
      const body = await responseBodySafe(verifyRes);
      lastFailure = `OTP verify returned ${verifyRes.status} on attempt ${attempt}: ${body}`;
      if (attempt < API_LOGIN_MAX_ATTEMPTS) {
        await sleep(API_LOGIN_RETRY_DELAY_MS);
        continue;
      }
    } else if (!verifyRes.ok) {
      const body = await responseBodySafe(verifyRes);
      throw new Error(`apiLogin OTP verify failed for ${email}: ${verifyRes.status} ${body}`);
    }

    // getSetCookie() returns each Set-Cookie header as a separate array entry,
    // avoiding the Node 20+ header-merging bug with headers.get('set-cookie').
    const setCookieHeaders = verifyRes.headers.getSetCookie();
    const sessionMatch = setCookieHeaders.find(h => h.includes('session='))?.match(/session=([^;]+)/);
    const xsrfMatch = setCookieHeaders.find(h => h.includes('XSRF-TOKEN='))?.match(/XSRF-TOKEN=([^;]+)/);

    // The verify endpoint currently returns an empty JSON object.
    const body = await verifyRes.json().catch(() => ({})) as { xsrf_token?: string };
    const xsrf = body.xsrf_token ?? xsrfMatch?.[1] ?? '';
    const session = sessionMatch?.[1] ?? '';

    if (session) {
      return { session, xsrf };
    }

    lastFailure = `session cookie missing on attempt ${attempt}`;
    if (attempt < API_LOGIN_MAX_ATTEMPTS) {
      await sleep(API_LOGIN_RETRY_DELAY_MS);
      continue;
    }
  }

  throw new Error(`apiLogin failed for ${email} after ${API_LOGIN_MAX_ATTEMPTS} attempts: ${lastFailure}`);
}

/** PATCH any resource on behalf of an authenticated user. */
export async function apiPatch(
  path: string,
  data: Record<string, unknown>,
  cookies: SessionCookies,
): Promise<Response> {
  return fetch(`${BACKEND_URL}${path}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Cookie': `session=${cookies.session}; XSRF-TOKEN=${cookies.xsrf}`,
      'X-XSRF-Token': cookies.xsrf,
    },
    body: JSON.stringify(data),
  });
}

/** DELETE a resource on behalf of an authenticated user. */
export async function apiDelete(path: string, cookies: SessionCookies): Promise<Response> {
  return fetch(`${BACKEND_URL}${path}`, {
    method: 'DELETE',
    headers: {
      'Cookie': `session=${cookies.session}; XSRF-TOKEN=${cookies.xsrf}`,
      'X-XSRF-Token': cookies.xsrf,
    },
  });
}

/** POST to a resource on behalf of an authenticated user (with optional JSON body). */
export async function apiPost(path: string, cookies: SessionCookies, data?: Record<string, unknown>): Promise<Response> {
  return fetch(`${BACKEND_URL}${path}`, {
    method: 'POST',
    headers: {
      ...(data ? { 'Content-Type': 'application/json' } : {}),
      'Cookie': `session=${cookies.session}; XSRF-TOKEN=${cookies.xsrf}`,
      'X-XSRF-Token': cookies.xsrf,
    },
    ...(data ? { body: JSON.stringify(data) } : {}),
  });
}

/** PUT a resource on behalf of an authenticated user. */
export async function apiPut(
  path: string,
  data: Record<string, unknown>,
  cookies: SessionCookies,
): Promise<Response> {
  return fetch(`${BACKEND_URL}${path}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Cookie': `session=${cookies.session}; XSRF-TOKEN=${cookies.xsrf}`,
      'X-XSRF-Token': cookies.xsrf,
    },
    body: JSON.stringify(data),
  });
}
