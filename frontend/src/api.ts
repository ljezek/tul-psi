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
  EvaluationOverviewResponse,
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

