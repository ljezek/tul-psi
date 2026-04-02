# Prompt 4: Student Zone — Home, Course Evaluation, Results

You are continuing development of the React frontend in `frontend/`. Phases 1-3 are complete — the app has working auth, login, dashboard, project cards, project detail, and nav with role-based content.

## Context

- Routes `/student`, `/student/project/:id/evaluate`, `/student/project/:id/results` are protected by `ProtectedRoute` with `allowedRoles={[UserRole.STUDENT]}`.
- `@/api` exports all API functions. Relevant for this phase:
  - `getProjects(filters)` — fetch all projects, can filter client-side by membership
  - `getProject(id)` — fetch project detail with evaluations if authenticated
  - `getCourseEvaluation(projectId)` — GET `/api/v1/projects/{id}/course-evaluation` (returns current draft or submitted evaluation)
  - `submitCourseEvaluation(projectId, data)` — PUT `/api/v1/projects/{id}/course-evaluation`
- `useAuth()` provides `user: UserPublic` which has `id`, `email`, `name`, `role`.
- Types in `@/types`: `ProjectPublic`, `CourseEvaluationSubmit`, `PeerFeedbackDetail`, `MemberPublic`, `CoursePublic`, etc.
- Backend `ProjectPublic` includes: `members` array (each has `id`), `course` with `project_type` (TEAM/INDIVIDUAL), `course.peer_bonus_budget` (null = no bonus points), `course.evaluation_criteria`, `results_unlocked`, `project_evaluations`, `received_peer_feedback`, `authored_peer_feedback`.
- Read `prototype/components/StudentZone.tsx` for the evaluation form design and the point distribution algorithm. This is the key reference.

## Important

- The course evaluation PUT body is `CourseEvaluationSubmit`:
```ts
{
  submitted: boolean,    // false = save draft, true = publish
  rating: number,        // 1-5
  strengths: string,
  improvements: string,
  peer_evaluations: {    // Only for TEAM projects
    receiving_student_id: number,
    strengths: string,
    improvements: string,
    bonus_points: number
  }[]
}
```

- The GET response for course evaluation returns the same shape (or null/404 if none exists yet).
- `project.course.peer_bonus_budget` controls the total bonus points budget. If null, no bonus points section.
- Peer evaluations are only for TEAM projects. For INDIVIDUAL, skip the peer section entirely.
- Point distribution: each teammate gets an equal share by default. When one slider changes, redistribute remaining proportionally among others. Port the algorithm from `prototype/components/StudentZone.tsx`.

## Task

### 1. Implement `src/pages/student/StudentHome.tsx`

Replace the placeholder. This is the student's landing page.

Requirements:
- Fetch all projects with `getProjects()` on mount.
- Filter to show only projects where the current user is a member: `project.members.some(m => m.id === user.id)`.
- If no projects: show "You are not assigned to any project" message with `t('student.no_project')`.
- For each project, show a card with:
  - Project title + course code + academic year.
  - Team members list (names).
  - Status indicators:
    - Evaluation: "Submitted" (green badge) if the user's course evaluation exists and is submitted. "Draft saved" (yellow badge) if exists but not submitted. "Not started" (gray badge) otherwise. Check `project.course_evaluations` for an entry with `student_id === user.id`.
    - Results: "Available" (green badge) if `results_unlocked === true`. "Pending" (gray) otherwise.
  - Action links:
    - "Submit Evaluation" → `/student/project/${id}/evaluate` (if not submitted yet)
    - "View Results" → `/student/project/${id}/results` (if results_unlocked)
- Use a clean card-based layout, similar to the Dashboard cards but with status badges.

Add translation keys as needed:
```
'student.evaluation_status': { cs: 'Stav hodnocení', en: 'Evaluation Status' }
'student.submitted': { cs: 'Odesláno', en: 'Submitted' }
'student.draft': { cs: 'Koncept uložen', en: 'Draft Saved' }
'student.not_started': { cs: 'Nezahájeno', en: 'Not Started' }
'student.results_available': { cs: 'Výsledky dostupné', en: 'Results Available' }
'student.results_pending': { cs: 'Výsledky čekají', en: 'Results Pending' }
'student.submit_evaluation': { cs: 'Odevzdat hodnocení', en: 'Submit Evaluation' }
'student.view_results': { cs: 'Zobrazit výsledky', en: 'View Results' }
```

### 2. Implement `src/pages/student/CourseEvaluation.tsx`

Replace the placeholder. This is the core evaluation form. **Reference `prototype/components/StudentZone.tsx` heavily.**

Requirements:
- Read `projectId` from URL params. Fetch `getProject(projectId)` on mount to get project details (course config, teammates).
- Also attempt to fetch existing evaluation with `getCourseEvaluation(projectId)`. If 404, start fresh. If data returned, populate form with existing values.
- **If already submitted** (evaluation exists with `submitted: true`): render read-only view of the submitted data. Do NOT allow editing.
- **Header**: project title, course name, "Course Evaluation" heading.
- **Back link**: to `/student`.

**Course Evaluation Section:**
- Rating: 1-5 scale. Use 5 clickable stars or radio buttons. Label: `t('student.subject_eval')`.
- Strengths textarea: label `t('student.subject_strengths')`.
- Improvements textarea: label `t('student.subject_improvements')`.

**Peer Evaluation Section** (only if `project.course.project_type === 'TEAM'`):
- Heading: `t('student.peer_eval')`.
- List teammates: filter `project.members` to exclude current user (`m.id !== user.id`).
- Per teammate card:
  - Name displayed.
  - Strengths textarea.
  - Improvements textarea.
  - Bonus points slider/input (only if `project.course.peer_bonus_budget !== null`):
    - Range: 0 to `peer_bonus_budget` (or some reasonable max like 20).
    - **Point distribution algorithm** (PORT FROM PROTOTYPE):
      - Total budget = `peer_bonus_budget` × number of teammates (or just `peer_bonus_budget` total — check the prototype logic).
      - Actually, looking at the prototype: `totalPoints = teammates.length * 10` and each slider is 0-20. The budget from the backend `peer_bonus_budget` replaces the hardcoded 10. So: `totalPoints = teammates.length * peer_bonus_budget`. Each slider range is 0 to `peer_bonus_budget * 2`.
      - When one slider changes: subtract its new value from total, distribute remainder proportionally among other teammates, respecting 0 to max bounds.
      - Show remaining points counter.
    - Default: each teammate gets `peer_bonus_budget` points (equal distribution).
- Anonymity notice: `t('student.disclaimer')`.

**Buttons:**
- "Save Draft" → `submitCourseEvaluation(projectId, { ...formData, submitted: false })`. Show success toast/message.
- "Submit" → `submitCourseEvaluation(projectId, { ...formData, submitted: true })`. Show confirmation dialog first ("This cannot be undone"). On success, switch to read-only view.

**Validation before submit:**
- Rating must be selected (1-5).
- Strengths and improvements must not be empty.
- For TEAM: all peer evaluation strengths and improvements must not be empty.
- Total bonus points must equal the budget (if bonus enabled).

### 3. Implement `src/pages/student/Results.tsx`

Replace the placeholder. Shows evaluation results when unlocked.

Requirements:
- Read `projectId` from URL params. Fetch `getProject(projectId)`.
- If `results_unlocked !== true`: show "Results are not yet available" message.
- **Back link**: to `/student`.
- **Lecturer Evaluation Section**:
  - Title: "Project Evaluation Results" or similar.
  - For each criterion in `project.course.evaluation_criteria`:
    - Show criterion description + max_score.
    - Average score across all `project_evaluations` for that criterion. Each `project_evaluation.scores` has entries with `criterion_code` matching `criterion.code`.
    - Show individual lecturer comments (strengths + improvements) per criterion.
  - **Total score**: sum of averaged criterion scores.
- **Peer Feedback Section** (if TEAM project):
  - Title: "Peer Feedback".
  - Show feedback received by current user from `received_peer_feedback`:
    - Each entry: strengths, improvements, bonus_points.
  - Average bonus points received.
- **Final Score**:
  - Total = average lecturer scores + average peer bonus points.
  - Compare against `project.course.min_score`.
  - Show pass/fail badge: green "PASS" if total >= min_score, red "FAIL" otherwise.
- Design: clean cards, color-coded scores (green for good, orange for medium, red for low relative to max).

Add translation keys as needed:
```
'results.title': { cs: 'Výsledky hodnocení', en: 'Evaluation Results' }
'results.not_available': { cs: 'Výsledky zatím nejsou k dispozici.', en: 'Results are not available yet.' }
'results.lecturer_eval': { cs: 'Hodnocení lektora', en: 'Lecturer Evaluation' }
'results.peer_feedback': { cs: 'Zpětná vazba kolegů', en: 'Peer Feedback' }
'results.total_score': { cs: 'Celkové skóre', en: 'Total Score' }
'results.pass': { cs: 'SPLNĚNO', en: 'PASS' }
'results.fail': { cs: 'NESPLNĚNO', en: 'FAIL' }
'results.avg_score': { cs: 'Průměrné skóre', en: 'Average Score' }
'results.avg_bonus': { cs: 'Průměrné bonusové body', en: 'Average Bonus Points' }
'results.min_required': { cs: 'Minimum k splnění', en: 'Minimum Required' }
```

## Constraints

- Use `@/*` import aliases.
- No `React` import needed.
- All user-visible strings through `t()`.
- No `any` types.
- Handle loading, error, and empty states.
- The point distribution algorithm is critical — test it manually (or add a unit test for the redistribution function if you extract it as a utility).

## Validation

```bash
cd frontend
npm run build
npm run lint
npm test
```
Fix all errors.
