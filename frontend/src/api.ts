import { config } from './config';
import {
  UserPublic,
  UserCreate,
  AdminUserUpdate,
  ProjectPublic,
  ProjectUpdate,
  AddMemberBody,
  CourseListItem,
  CourseDetail,
  CourseCreate,
  CourseUpdate,
  CourseLecturerPublic,
  ProjectCreate,
  ProjectEvaluationDetail,
  ProjectEvaluationCreate,
  CourseEvaluationSubmit,
  CourseEvaluationFormResponse,
  CourseTerm,
  MemberPublic,
  AnnouncementPublic,
  AnnouncementCreate,
  AnnouncementUpdate,
} from './types';

// ---------------------------------------------------------------------------
// CSRF token store
//
// The XSRF-TOKEN cookie is set on the *backend* domain, so document.cookie on
// the frontend (SWA) domain cannot read it.  Instead, verify_otp returns the
// token in the response body, and we persist it in localStorage so that it
// survives page refreshes and is shared across tabs.
// ---------------------------------------------------------------------------
const _CSRF_STORAGE_KEY = 'xsrf-token';
// In-memory fallback for environments where localStorage is unavailable (e.g. private browsing
// with strict storage blocking).  Under normal conditions the token is always read fresh from
// localStorage on each request so that cross-tab logout/login stays consistent.
let _csrfTokenFallback: string | null = null;

export function getStoredCsrfToken(): string | null {
  try { return localStorage.getItem(_CSRF_STORAGE_KEY); } catch { return _csrfTokenFallback; }
}

export function storeCsrfToken(token: string): void {
  _csrfTokenFallback = token;
  try { localStorage.setItem(_CSRF_STORAGE_KEY, token); } catch { /* storage unavailable */ }
}

function clearCsrfToken(): void {
  _csrfTokenFallback = null;
  try { localStorage.removeItem(_CSRF_STORAGE_KEY); } catch { /* storage unavailable */ }
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  code?: string;

  constructor(status: number, detail: unknown, code?: string) {
    super(`API Error: ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.code = code;
  }
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);
// Allow extra time for the backend to cold-start (minReplicas=0 in Azure Container Apps).
const REQUEST_TIMEOUT_MS = 60_000;

async function apiFetch<T>(path: string, options: NonNullable<Parameters<typeof fetch>[1]> = {}): Promise<T> {
  const url = `${config.apiUrl}${path}`;
  const headers = new Headers(options.headers);

  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  if (MUTATING_METHODS.has((options.method ?? 'GET').toUpperCase())) {
    const xsrfToken = getStoredCsrfToken() || getCookie('XSRF-TOKEN');
    if (xsrfToken) {
      headers.set('X-XSRF-Token', xsrfToken);
    }
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include',
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(408, null, 'request_timeout');
    }
    throw err;
  }
  clearTimeout(timeoutId);

  if (!response.ok) {
    const errorText = await response.text();
    let detail: unknown = errorText;

    if (errorText) {
      try {
        detail = JSON.parse(errorText);
      } catch {
        detail = errorText;
      }
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  // Handle empty JSON responses
  const text = await response.text();
  return text ? JSON.parse(text) : ({} as T);
}

export async function requestOtp(email: string): Promise<{ message: string }> {
  return apiFetch<{ message: string }>('/api/v1/auth/otp/request', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

export async function verifyOtp(email: string, otp: string): Promise<{ xsrf_token: string }> {
  return apiFetch<{ xsrf_token: string }>('/api/v1/auth/otp/verify', {
    method: 'POST',
    body: JSON.stringify({ email, otp }),
  });
}

export async function logout(): Promise<void> {
  try {
    await apiFetch<void>('/api/v1/auth/logout', { method: 'POST' });
  } finally {
    clearCsrfToken();
  }
}

export async function refreshCsrfToken(): Promise<void> {
  const { xsrf_token } = await apiFetch<{ xsrf_token: string }>('/api/v1/auth/csrf-token');
  storeCsrfToken(xsrf_token);
}

export async function getUsers(): Promise<UserPublic[]> {
  return apiFetch<UserPublic[]>('/api/v1/users');
}

export async function createUser(data: UserCreate): Promise<UserPublic> {
  return apiFetch<UserPublic>('/api/v1/users', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getCurrentUser(): Promise<UserPublic> {
  return apiFetch<UserPublic>('/api/v1/users/me');
}

export async function updateCurrentUser(data: { name?: string; github_alias?: string | null }): Promise<UserPublic> {
  return apiFetch<UserPublic>('/api/v1/users/me', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function updateUser(id: number, data: AdminUserUpdate): Promise<UserPublic> {
  return apiFetch<UserPublic>(`/api/v1/users/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function getProjects(filters?: { q?: string; course?: string; year?: number; term?: CourseTerm; technology?: string }): Promise<ProjectPublic[]> {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, String(value));
      }
    });
  }
  const queryString = params.toString();
  const path = `/api/v1/projects${queryString ? `?${queryString}` : ''}`;
  return apiFetch<ProjectPublic[]>(path);
}

export async function getProject(id: number): Promise<ProjectPublic> {
  return apiFetch<ProjectPublic>(`/api/v1/projects/${id}`);
}

export async function updateProject(id: number, data: ProjectUpdate): Promise<ProjectPublic> {
  return apiFetch<ProjectPublic>(`/api/v1/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function addProjectMember(projectId: number, data: AddMemberBody): Promise<MemberPublic> {
  return apiFetch<MemberPublic>(`/api/v1/projects/${projectId}/members`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getCourses(): Promise<CourseListItem[]> {
  return apiFetch<CourseListItem[]>('/api/v1/courses');
}

export async function getCourse(id: number): Promise<CourseDetail> {
  return apiFetch<CourseDetail>(`/api/v1/courses/${id}`);
}

export async function createCourse(data: CourseCreate): Promise<CourseDetail> {
  return apiFetch<CourseDetail>('/api/v1/courses', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateCourse(id: number, data: CourseUpdate): Promise<CourseDetail> {
  return apiFetch<CourseDetail>(`/api/v1/courses/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function addCourseLecturer(courseId: number, data: AddMemberBody): Promise<CourseLecturerPublic> {
  return apiFetch<CourseLecturerPublic>(`/api/v1/courses/${courseId}/lecturers`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteCourseLecturer(courseId: number, userId: number): Promise<void> {
  return apiFetch<void>(`/api/v1/courses/${courseId}/lecturers/${userId}`, {
    method: 'DELETE',
  });
}

export async function createCourseProject(courseId: number, data: ProjectCreate): Promise<ProjectPublic> {
  return apiFetch<ProjectPublic>(`/api/v1/courses/${courseId}/projects`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getProjectEvaluation(projectId: number): Promise<ProjectEvaluationDetail> {
  return apiFetch<ProjectEvaluationDetail>(`/api/v1/projects/${projectId}/project-evaluation`);
}

export async function submitProjectEvaluation(projectId: number, data: ProjectEvaluationCreate): Promise<ProjectEvaluationDetail> {
  return apiFetch<ProjectEvaluationDetail>(`/api/v1/projects/${projectId}/project-evaluation`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function unlockProject(projectId: number): Promise<ProjectPublic> {
  return apiFetch<ProjectPublic>(`/api/v1/projects/${projectId}/unlock`, {
    method: 'POST',
  });
}

export async function lockProject(projectId: number): Promise<ProjectPublic> {
  return apiFetch<ProjectPublic>(`/api/v1/projects/${projectId}/lock`, {
    method: 'POST',
  });
}

export async function getCourseEvaluation(projectId: number): Promise<CourseEvaluationFormResponse> {
  return apiFetch<CourseEvaluationFormResponse>(`/api/v1/projects/${projectId}/course-evaluation`);
}

export async function submitCourseEvaluation(projectId: number, data: CourseEvaluationSubmit): Promise<void> {
  return apiFetch<void>(`/api/v1/projects/${projectId}/course-evaluation`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteProject(projectId: number): Promise<void> {
  const path = `/api/v1/projects/${projectId}`;
  return apiFetch<void>(path, { method: 'DELETE' });
}

export async function deleteProjectMember(projectId: number, userId: number): Promise<void> {
  const path = `/api/v1/projects/${projectId}/members/${userId}`;
  return apiFetch<void>(path, { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// Announcements
// ---------------------------------------------------------------------------

export async function getActiveAnnouncement(): Promise<AnnouncementPublic | null> {
  return apiFetch<AnnouncementPublic | null>('/api/v1/announcements/active');
}

export async function getAnnouncements(): Promise<AnnouncementPublic[]> {
  return apiFetch<AnnouncementPublic[]>('/api/v1/announcements');
}

export async function createAnnouncement(data: AnnouncementCreate): Promise<AnnouncementPublic> {
  return apiFetch<AnnouncementPublic>('/api/v1/announcements', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateAnnouncement(id: number, data: AnnouncementUpdate): Promise<AnnouncementPublic> {
  return apiFetch<AnnouncementPublic>(`/api/v1/announcements/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteAnnouncement(id: number): Promise<void> {
  return apiFetch<void>(`/api/v1/announcements/${id}`, { method: 'DELETE' });
}

