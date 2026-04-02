# Prompt 5: Lecturer Panel — Home, Course Projects, Project Evaluation

You are continuing development of the React frontend in `frontend/`. Phases 1-4 are complete — the app has working auth, dashboard, project browser/detail, login, student zone with evaluation form and results.

## Context

- Routes `/lecturer`, `/lecturer/course/:id`, `/lecturer/project/:id/evaluate` are protected by `ProtectedRoute` for LECTURER and ADMIN roles.
- `@/api` exports. Relevant for this phase:
  - `getCourses()` → `CourseListItem[]` (has `id`, `code`, `name`, `lecturer_names`, `stats`)
  - `getCourse(id)` → `CourseDetail` (has `lecturers` with `id`, `name`, `email`)
  - `getProjects({ course, year })` → `ProjectPublic[]`
  - `getProject(id)` → `ProjectPublic` (with evaluation data when authenticated)
  - `createCourseProject(courseId, data)` → `ProjectPublic`
  - `addProjectMember(projectId, data)` → `MemberPublic`
  - `getProjectEvaluation(projectId)` → `ProjectEvaluationDetail` (404 if none exists)
  - `submitProjectEvaluation(projectId, data)` → `ProjectEvaluationDetail`
  - `unlockProject(projectId)` → `ProjectPublic`
- `useAuth()` provides `user: UserPublic`.
- Types: `CourseListItem`, `CourseDetail`, `ProjectPublic`, `ProjectEvaluationCreate`, `ProjectEvaluationDetail`, `ProjectCreate`, `AddMemberBody`, `EvaluationCriterion`.

## Task

### 1. Implement `src/pages/lecturer/LecturerHome.tsx`

Replace the placeholder. This is the lecturer's landing page.

Requirements:
- Fetch all courses with `getCourses()` on mount.
- Filter to show only courses where the current user is a lecturer: check `course.lecturer_names` includes `user.name` (imperfect but sufficient), OR fetch course detail and check lecturers list. The simpler approach: show all courses and let the backend handle permissions on the per-course actions.
- **Better approach**: Show all courses (the list is small), but highlight the ones where the user is a lecturer.
- Each course card shows:
  - Course code (large, bold) + course name.
  - Lecturer names (comma-separated).
  - Stats: project count, academic years.
  - "Manage Projects" link → `/lecturer/course/${course.id}`.
- If no courses: show an info message.
- Design: clean card grid, similar to dashboard. Use `lucide-react` `BookOpen`, `Users`, `FolderOpen` icons.

Add translation keys:
```
'lecturer.title': { cs: 'Panel lektora', en: 'Lecturer Panel' }
'lecturer.subtitle': { cs: 'Spravujte kurzy a hodnoťte projekty.', en: 'Manage courses and evaluate projects.' }
'lecturer.manage_projects': { cs: 'Spravovat projekty', en: 'Manage Projects' }
'lecturer.project_count': { cs: 'Počet projektů', en: 'Project Count' }
'lecturer.academic_years': { cs: 'Akademické roky', en: 'Academic Years' }
'lecturer.no_courses': { cs: 'Žádné kurzy k dispozici.', en: 'No courses available.' }
```

### 2. Implement `src/pages/lecturer/CourseProjects.tsx`

Replace the placeholder. Shows all projects for a specific course, and allows creating new ones.

Requirements:
- Read `courseId` from URL params (`:id`). Fetch `getCourse(courseId)` and `getProjects({ course: courseDetail.code })` on mount.
- **Back link**: to `/lecturer`.
- **Course header**: course code + name, term, project_type, lecturers.
- **Year filter**: dropdown of academic years from the course stats + a "current year" option. Filters the project list.
- **Project list** (table or card layout):
  - Each project: title, academic year, members (names), evaluation status.
  - Evaluation status per project: 
    - Check `project.project_evaluations` for current user's evaluation. Show "Submitted" (green), "Draft" (yellow), or "Not evaluated" (gray).
    - Show if project results are unlocked (green badge).
  - Action buttons:
    - "Evaluate" → `/lecturer/project/${project.id}/evaluate`
    - "Unlock Results" button (visible only if not already unlocked) → calls `unlockProject(project.id)`, then refresh.
  - "Add Member" action per project: small form or modal to add a student by email → `addProjectMember(projectId, { email, name?, github_alias? })`.
- **Add Project section** (form or expandable section):
  - Fields: title (required), academic_year (required, default: current year e.g. 2025), owner_email (optional, @tul.cz).
  - Description, github_url, live_url, technologies (comma-separated) — optional fields.
  - Submit → `createCourseProject(courseId, data)`. On success, refresh project list. Show success message.
  - On 403: show permission error. On 404: course not found.
- Loading and error states.

Add translation keys:
```
'lecturer.course_projects': { cs: 'Projekty kurzu', en: 'Course Projects' }
'lecturer.add_project': { cs: 'Přidat projekt', en: 'Add Project' }
'lecturer.add_member': { cs: 'Přidat člena', en: 'Add Member' }
'lecturer.unlock_results': { cs: 'Odemknout výsledky', en: 'Unlock Results' }
'lecturer.results_unlocked': { cs: 'Výsledky odemčeny', en: 'Results Unlocked' }
'lecturer.evaluate': { cs: 'Hodnotit', en: 'Evaluate' }
'lecturer.eval_submitted': { cs: 'Odesláno', en: 'Submitted' }
'lecturer.eval_draft': { cs: 'Koncept', en: 'Draft' }
'lecturer.eval_not_done': { cs: 'Nehodnoceno', en: 'Not Evaluated' }
'lecturer.project_title': { cs: 'Název projektu', en: 'Project Title' }
'lecturer.owner_email': { cs: 'Email vlastníka projektu', en: 'Project Owner Email' }
```

### 3. Implement `src/pages/lecturer/ProjectEvaluation.tsx`

Replace the placeholder. The lecturer evaluation form for a specific project.

Requirements:
- Read `projectId` from URL params. Fetch `getProject(projectId)` to get course config and `getProjectEvaluation(projectId)` to get existing evaluation (404 if none).
- **Back link**: to `/lecturer/course/${project.course_id}` — but we don't have course_id directly. Use `/lecturer` as fallback, or extract from the course detail. Add `// TODO: navigate back to course page` if needed.
- **Header**: project title, course code, team members list.
- **Evaluation form**: one section per criterion from `project.course.evaluation_criteria`.
  - Each criterion:
    - Criterion description (label).
    - Score input: number input, min 0, max = `criterion.max_score`. Show ` / {max_score}` next to input.
    - Strengths textarea.
    - Improvements textarea.
  - Pre-fill from existing evaluation data if available. Match by `criterion_code`.
- **Buttons**:
  - "Save Draft" → `submitProjectEvaluation(projectId, { scores: [...], submitted: false })`.
  - "Submit" → `submitProjectEvaluation(projectId, { scores: [...], submitted: true })`. Confirmation dialog first.
  - If already submitted and results not unlocked, allow re-editing (the backend handles upsert). If results are unlocked (409 from backend), show error.
- **Read-only mode**: if the project evaluation is already submitted AND results are unlocked, render as read-only.
- **Validation**: all scores must be between 0 and max_score. All strengths/improvements fields must be non-empty.
- Error handling: 403 (not authorized), 404 (project not found), 409 (results already unlocked), 422 (invalid data).

Add translation keys:
```
'lecturer.project_evaluation': { cs: 'Hodnocení projektu', en: 'Project Evaluation' }
'lecturer.criterion': { cs: 'Kritérium', en: 'Criterion' }
'lecturer.score': { cs: 'Skóre', en: 'Score' }
'lecturer.save_draft': { cs: 'Uložit koncept', en: 'Save Draft' }
'lecturer.submit_evaluation': { cs: 'Odevzdat hodnocení', en: 'Submit Evaluation' }
'lecturer.confirm_submit': { cs: 'Opravdu chcete odevzdat? Tuto akci nelze vrátit.', en: 'Are you sure? This cannot be undone.' }
'lecturer.eval_locked': { cs: 'Výsledky jsou odemčeny, hodnocení nelze upravit.', en: 'Results are unlocked, evaluation cannot be edited.' }
```

## Constraints

- Use `@/*` import aliases.
- No `React` import needed.
- All user-visible strings through `t()`.
- No `any` types.
- Handle loading, error, and empty states.
- Add `// TODO:` comments for: evaluation overview table (stretch goal), course editing (admin only).

## Validation

```bash
cd frontend
npm run build
npm run lint
npm test
```
Fix all errors.
