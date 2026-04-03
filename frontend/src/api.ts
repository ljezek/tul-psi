import { config } from './config';
import {
  UserPublic,
  ProjectPublic,
  ProjectUpdate,
  AddMemberBody,
  CourseListItem,
  CourseDetail,
  ProjectCreate,
  ProjectEvaluationDetail,
  ProjectEvaluationCreate,
  CourseEvaluationSubmit,
  CourseTerm,
  MemberPublic
} from './types';

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(`API Error: ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function apiFetch<T>(path: string, options: NonNullable<Parameters<typeof fetch>[1]> = {}): Promise<T> {
  const url = `${config.apiUrl}${path}`;
  const headers = new Headers(options.headers);

  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  // TODO: Add XSRF token header for state-changing requests
  
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

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

export async function verifyOtp(email: string, otp: string): Promise<Record<string, never>> {
  return apiFetch<Record<string, never>>('/api/v1/auth/otp/verify', {
    method: 'POST',
    body: JSON.stringify({ email, otp }),
  });
}

export async function logout(): Promise<void> {
  return apiFetch<void>('/api/v1/auth/logout', {
    method: 'POST',
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

// TODO: The course-evaluation endpoints below are not yet implemented in the backend.
// They will return 404 until the corresponding routes are added (tracked in a separate PR).

export async function getCourseEvaluation(projectId: number): Promise<CourseEvaluationSubmit> {
  return apiFetch<CourseEvaluationSubmit>(`/api/v1/projects/${projectId}/course-evaluation`);
}

export async function submitCourseEvaluation(projectId: number, data: CourseEvaluationSubmit): Promise<void> {
  return apiFetch<void>(`/api/v1/projects/${projectId}/course-evaluation`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}
