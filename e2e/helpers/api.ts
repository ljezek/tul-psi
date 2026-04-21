/**
 * Thin wrappers around direct backend API calls.
 * Used in afterAll hooks to restore seeded state after mutating tests.
 */

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8001';

interface SessionCookies {
  session: string;
  xsrf: string;
}

/** Log in via the API (not the browser) and return raw session cookies. */
export async function apiLogin(email: string): Promise<SessionCookies> {
  // Step 1: request OTP
  await fetch(`${BACKEND_URL}/api/v1/auth/otp/request`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });

  // Step 2: verify OTP (E2E_OTP_OVERRIDE=000000)
  const verifyRes = await fetch(`${BACKEND_URL}/api/v1/auth/otp/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp: '000000' }),
  });

  if (!verifyRes.ok) {
    throw new Error(`apiLogin failed for ${email}: ${verifyRes.status}`);
  }

  const setCookieHeader = verifyRes.headers.get('set-cookie') ?? '';
  const sessionMatch = setCookieHeader.match(/session=([^;]+)/);
  const xsrfMatch = setCookieHeader.match(/XSRF-TOKEN=([^;]+)/);

  // The XSRF token is also in the response body
  const body = await verifyRes.json() as { xsrf_token?: string };
  const xsrf = body.xsrf_token ?? xsrfMatch?.[1] ?? '';
  const session = sessionMatch?.[1] ?? '';

  return { session, xsrf };
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

/** POST to a resource on behalf of an authenticated user (no body). */
export async function apiPost(path: string, cookies: SessionCookies): Promise<Response> {
  return fetch(`${BACKEND_URL}${path}`, {
    method: 'POST',
    headers: {
      'Cookie': `session=${cookies.session}; XSRF-TOKEN=${cookies.xsrf}`,
      'X-XSRF-Token': cookies.xsrf,
    },
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
