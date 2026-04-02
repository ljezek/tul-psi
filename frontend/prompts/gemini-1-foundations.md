# Prompt 1: Foundation — Types, API Client, Contexts, Router, UI Components

You are building the production React frontend for the **Student Projects Catalogue** at TUL. The project directory is `frontend/`. There is a working prototype in `prototype/` — use it as a UI/UX reference but do NOT modify it. The backend is a FastAPI app in `backend/`.

## Context

- React 19, TypeScript 5 (strict), Vite 6, Tailwind CSS 3
- Path alias `@/*` → `src/*` is already configured in `tsconfig.json` and `vite.config.ts`
- `tailwind.config.js` has a custom `tul-blue` (#0077c8) color and Inter font
- The backend API is at `VITE_API_URL` (default `http://localhost:8000`), all endpoints prefixed `/api/v1`
- Authentication is cookie-based: the backend sets an HttpOnly `session` cookie after OTP verification
- There is NO logout endpoint on the backend — implement logout by deleting the `session` cookie client-side
- Read `prototype/LanguageContext.tsx` and `prototype/components/Button.tsx` for reference patterns

## Task

### 1. Install dependencies

```bash
cd frontend
npm install react-router-dom lucide-react
```

### 2. Create `src/types.ts`

Define TypeScript types matching the backend schemas exactly (snake_case field names — no camelCase transformation). Read `backend/schemas/projects.py`, `backend/schemas/courses.py`, `backend/schemas/users.py`, and `backend/models/course.py` for exact field names.

Required types:
```
// Enums
enum UserRole { ADMIN = "ADMIN", LECTURER = "LECTURER", STUDENT = "STUDENT" }
enum CourseTerm { SUMMER = "SUMMER", WINTER = "WINTER" }
enum ProjectType { TEAM = "TEAM", INDIVIDUAL = "INDIVIDUAL" }

// From schemas/users.py
interface UserPublic { id: number; email: string; github_alias: string | null; name: string; role: UserRole; is_active: boolean }

// From schemas/projects.py
interface LecturerPublic { name: string; github_alias: string | null; email: string | null }
interface MemberPublic { id: number; github_alias: string | null; name: string; email: string | null }
interface EvaluationCriterion { code: string; description: string; max_score: number }
interface CourseLink { label: string; url: string }
interface CoursePublic { code: string; name: string; syllabus: string | null; term: CourseTerm; project_type: ProjectType; min_score: number; peer_bonus_budget: number | null; evaluation_criteria: EvaluationCriterion[]; links: CourseLink[]; lecturers: LecturerPublic[] }
interface MemberPublic { id: number; github_alias: string | null; name: string; email: string | null }
interface EvaluationScoreDetail { criterion_code: string; score: number; strengths: string; improvements: string }
interface ProjectEvaluationDetail { lecturer_id: number; scores: EvaluationScoreDetail[]; updated_at: string; submitted: boolean }
interface CourseEvaluationDetail { id: number; student_id: number; rating: number; strengths: string | null; improvements: string | null; submitted: boolean; updated_at: string }
interface PeerFeedbackDetail { course_evaluation_id: number; receiving_student_id: number; strengths: string | null; improvements: string | null; bonus_points: number }
interface ProjectPublic { id: number; title: string; description: string | null; github_url: string | null; live_url: string | null; technologies: string[]; academic_year: number; course: CoursePublic; members: MemberPublic[]; results_unlocked: boolean | null; project_evaluations: ProjectEvaluationDetail[] | null; course_evaluations: CourseEvaluationDetail[] | null; received_peer_feedback: PeerFeedbackDetail[] | null; authored_peer_feedback: PeerFeedbackDetail[] | null }

// From schemas/courses.py
interface CourseStats { project_count: number; academic_years: number[] }
interface CourseListItem { id: number; code: string; name: string; syllabus: string | null; lecturer_names: string[]; stats: CourseStats }

// Request types
interface ProjectEvaluationCreate { scores: { criterion_code: string; score: number; strengths: string; improvements: string }[]; submitted: boolean }
interface ProjectCreate { title: string; description?: string | null; github_url?: string | null; live_url?: string | null; technologies?: string[]; academic_year: number; owner_email?: string | null }
interface ProjectUpdate { title?: string | null; description?: string | null; github_url?: string | null; live_url?: string | null; technologies?: string[] | null }
interface AddMemberBody { email: string; name?: string | null; github_alias?: string | null }

// Course evaluation (student submission)
interface CourseEvaluationSubmit { submitted: boolean; rating: number; strengths: string; improvements: string; peer_evaluations: { receiving_student_id: number; strengths: string; improvements: string; bonus_points: number }[] }
```

Export all types.

### 3. Create `src/api.ts`

Typed API client using `fetch`. Read `src/config.ts` for the `apiUrl` base.

Requirements:
- Generic helper: `async function apiFetch<T>(path: string, options?: RequestInit): Promise<T>` that:
  - Prepends `config.apiUrl` to the path
  - Sets `credentials: 'include'` (cookie auth)
  - Sets `Content-Type: application/json` for requests with body
  - Throws an `ApiError` class (with `status` and `detail` fields) on non-2xx responses
  - For 204 responses, returns `undefined as T`
- Export named functions for each endpoint:
  - `requestOtp(email: string): Promise<{ message: string }>`  — POST `/api/v1/auth/otp/request`
  - `verifyOtp(email: string, otp: string): Promise<void>` — POST `/api/v1/auth/otp/verify`
  - `getCurrentUser(): Promise<UserPublic>` — GET `/api/v1/users/me`
  - `updateCurrentUser(data: { name?: string; github_alias?: string | null }): Promise<UserPublic>` — PATCH `/api/v1/users/me`
  - `getProjects(filters?: { q?: string; course?: string; year?: number; term?: CourseTerm; technology?: string }): Promise<ProjectPublic[]>` — GET `/api/v1/projects` with query params
  - `getProject(id: number): Promise<ProjectPublic>` — GET `/api/v1/projects/{id}`
  - `updateProject(id: number, data: ProjectUpdate): Promise<ProjectPublic>` — PATCH `/api/v1/projects/{id}`
  - `addProjectMember(projectId: number, data: AddMemberBody): Promise<MemberPublic>` — POST `/api/v1/projects/{id}/members`
  - `getCourses(): Promise<CourseListItem[]>` — GET `/api/v1/courses`
  - `getCourse(id: number): Promise<CourseDetail>` — GET `/api/v1/courses/{id}` (add CourseDetail to types if missing — it's id + code + name + syllabus + term + project_type + min_score + peer_bonus_budget + evaluation_criteria + links + lecturers + course_evaluations)
  - `createCourseProject(courseId: number, data: ProjectCreate): Promise<ProjectPublic>` — POST `/api/v1/courses/{courseId}/projects`
  - `getProjectEvaluation(projectId: number): Promise<ProjectEvaluationDetail>` — GET `/api/v1/projects/{id}/project-evaluation`
  - `submitProjectEvaluation(projectId: number, data: ProjectEvaluationCreate): Promise<ProjectEvaluationDetail>` — POST `/api/v1/projects/{id}/project-evaluation`
  - `unlockProject(projectId: number): Promise<ProjectPublic>` — POST `/api/v1/projects/{id}/unlock`
  - `getCourseEvaluation(projectId: number): Promise<CourseEvaluationSubmit>` — GET `/api/v1/projects/{id}/course-evaluation` (TODO: backend endpoint in progress)
  - `submitCourseEvaluation(projectId: number, data: CourseEvaluationSubmit): Promise<void>` — PUT `/api/v1/projects/{id}/course-evaluation` (TODO: backend endpoint in progress)
- For `getProjects`, build the query string from non-undefined filter values.

### 4. Create `src/contexts/AuthContext.tsx`

Authentication context. Pattern:
- On mount: call `getCurrentUser()`. If 200, store `UserPublic` in state. If error (401), set `user = null`.
- Expose via context: `user: UserPublic | null`, `loading: boolean`, `login(email: string, otp: string): Promise<void>` (calls `verifyOtp`, then refetches `getCurrentUser`), `logout(): void` (delete `session` cookie by setting `document.cookie = 'session=; Max-Age=0; path=/;'`, set user to null), `refreshUser(): Promise<void>`.
- Wrap children with the provider. Show nothing (or a spinner) until initial auth check completes.
- Export `useAuth()` hook that throws if used outside provider.

### 5. Create `src/contexts/LanguageContext.tsx` and `src/contexts/LanguageContext.test.tsx`

Port from `prototype/LanguageContext.tsx` and `prototype/LanguageContext.test.tsx`. Keep all existing translation keys. Add any new keys needed (you can add more later).

The test file should work with the `@testing-library/react` and `vitest` setup already configured. Match the patterns from the prototype test exactly but adapt imports to use `@/contexts/LanguageContext` path alias.

### 6. Create `src/layouts/MainLayout.tsx`

Application shell with navigation bar and footer. Reference `prototype/App.tsx` for the nav design.

Requirements:
- Import `Outlet` from `react-router-dom` and render it in the main content area.
- Navigation bar:
  - Left: TUL logo placeholder (the "FM" square in `tul-blue` as in current App.tsx) + app title from `t('app.title')`.
  - Center/Right: Navigation links based on auth state:
    - Always: "Dashboard" link to `/`
    - Authenticated student: "Student Zone" link to `/student`
    - Authenticated lecturer/admin: "Lecturer Panel" link to `/lecturer`
  - Right: Language toggle button (CS/EN), auth status (login link or user name + role badge + logout button)
  - Mobile: hamburger menu with same items
- Footer: copyright text from `t('footer.copyright')`
- Use `lucide-react` icons: `Menu`, `X`, `Globe`, `LogIn`, `LogOut`, `User` as appropriate
- Tailwind styling matching the prototype's aesthetic (white bg nav, shadow-sm, sticky top)

### 7. Create `src/components/ProtectedRoute.tsx`

Route guard component:
- Takes `allowedRoles?: UserRole[]` prop
- Uses `useAuth()` to check authentication
- If `loading`, show a spinner
- If not authenticated, redirect to `/login` using `Navigate` from react-router-dom
- If `allowedRoles` specified and user's role not in list, redirect to `/`
- Otherwise render `<Outlet />`

### 8. Create `src/components/ui/Button.tsx`

Port from `prototype/components/Button.tsx`. Same variants (primary/secondary/outline/ghost), sizes (sm/md/lg), and extends `ButtonHTMLAttributes<HTMLButtonElement>`. Use `@/` import path alias for any internal imports.

### 9. Create `src/components/ui/LoadingSpinner.tsx`

Simple centered spinner component. A `div` with `animate-spin rounded-full border-4 border-slate-200 border-t-tul-blue h-8 w-8`. Accepts optional `className` prop.

### 10. Create `src/components/ui/ErrorMessage.tsx`

Error display component with props: `message: string`, `onRetry?: () => void`. Shows an alert icon, the message text, and optionally a "Retry" button.

### 11. Update `src/App.tsx`

Replace the stub with the router setup:

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
// Import contexts and layouts
// Wrap everything in: LanguageProvider → AuthProvider → BrowserRouter
// Routes:
//   <Route element={<MainLayout />}>
//     <Route path="/" element={<Dashboard />} />
//     <Route path="/login" element={<LoginPage />} />
//     <Route path="/projects/:id" element={<ProjectDetail />} />
//     <Route element={<ProtectedRoute allowedRoles={[UserRole.STUDENT]} />}>
//       <Route path="/student" element={<StudentHome />} />
//       <Route path="/student/project/:id/evaluate" element={<CourseEvaluation />} />
//       <Route path="/student/project/:id/results" element={<Results />} />
//     </Route>
//     <Route element={<ProtectedRoute allowedRoles={[UserRole.LECTURER, UserRole.ADMIN]} />}>
//       <Route path="/lecturer" element={<LecturerHome />} />
//       <Route path="/lecturer/course/:id" element={<CourseProjects />} />
//       <Route path="/lecturer/project/:id/evaluate" element={<ProjectEvaluation />} />
//     </Route>
//   </Route>
```

For pages that don't exist yet, create minimal placeholder components in their respective files that just render a heading with the page name. This ensures the app compiles. Create these placeholder files:
- `src/pages/Dashboard.tsx` — `<h1>{t('dashboard.title')}</h1>`
- `src/pages/Login.tsx` — `<h1>Login</h1>`
- `src/pages/ProjectDetail.tsx` — `<h1>Project Detail</h1>`
- `src/pages/student/StudentHome.tsx` — `<h1>{t('student.zone_title')}</h1>`
- `src/pages/student/CourseEvaluation.tsx` — `<h1>Course Evaluation</h1>`
- `src/pages/student/Results.tsx` — `<h1>Results</h1>`
- `src/pages/lecturer/LecturerHome.tsx` — `<h1>Lecturer Panel</h1>`
- `src/pages/lecturer/CourseProjects.tsx` — `<h1>Course Projects</h1>`
- `src/pages/lecturer/ProjectEvaluation.tsx` — `<h1>Project Evaluation</h1>`

### 12. Update `src/App.test.tsx`

Update the test to work with the new App that includes router and providers. The test should:
- Render `<App />` (which now includes BrowserRouter and providers internally)
- Assert that the app title or nav heading renders (since the initial route is `/` which shows Dashboard)
- May need to mock the API call to `/users/me` (mock fetch to return 401 for unauthenticated state)

## Constraints

- Use `@/*` import aliases for all internal imports (e.g., `import { useAuth } from '@/contexts/AuthContext'`).
- No `React` import needed (JSX transform configured).
- All user-visible strings must use the `t()` function from LanguageContext. If a key doesn't exist yet, add it to the translations.
- No `any` types. No `as` casts without a `// TODO:` comment justifying it.
- Add `// TODO:` comments for known shortcuts (e.g., `// TODO: Add XSRF token header for state-changing requests`).
- Name component prop interfaces as `ComponentNameProps`.

## Validation

After completing all steps, run:
```bash
cd frontend
npm run build
npm run lint
npm test
```
Fix any errors until all three commands pass cleanly. Warnings are acceptable.
