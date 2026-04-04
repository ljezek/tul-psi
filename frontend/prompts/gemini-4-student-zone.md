# Prompt 4: Student Zone — Home, Course Evaluation, Results

You are continuing development of the React frontend in `frontend/`. Phases 1-3 are complete — the app has working auth, login, dashboard, project cards, project detail, a dedicated `/profile` page, and a navigation bar with role-based links.

## Context

- Routes `/student`, `/student/project/:id/evaluate`, `/student/project/:id/results` are protected by `ProtectedRoute` with `allowedRoles={[UserRole.STUDENT]}`.
- `@/api` exports all API functions. Relevant for this phase:
  - `getProjects(filters)` — fetch all projects, can filter client-side by membership.
  - `getProject(id)` — fetch project detail with evaluations if authenticated.
  - `getCourseEvaluation(projectId)` — GET `/api/v1/projects/{id}/course-evaluation`.
  - `submitCourseEvaluation(projectId, data)` — PUT `/api/v1/projects/{id}/course-evaluation`.
- `useAuth()` provides `user: UserPublic` with `id`, `email`, `name`, `role`.
- Use existing UI components: `Button`, `LoadingSpinner`, `ErrorMessage`, and `@/components/icons/GitHubLogo`.
- Point distribution algorithm: port and refine the proportional redistribution logic from `prototype/components/StudentZone.tsx`.

## Technical Requirements

### 1. Reusable Evaluation Components
Extract the proportional redistribution logic into a utility or a custom hook `usePointRedistribution`. 
- **Total Budget**: `teammates.length * peer_bonus_budget`.
- **Max per Person**: `peer_bonus_budget * 2`.
- **Logic**: When one value changes, adjust others proportionally to keep the total constant, respecting [0, max] bounds.

### 2. Implement `src/pages/student/StudentHome.tsx`

The landing page for authenticated students.

Requirements:
- Fetch all projects using `getProjects()`. Filter client-side: `project.members.some(m => m.id === user.id)`.
- If no projects: show `t('student.no_project')`.
- For each project, show a card with:
  - Title, Course Code, Year.
  - **Evaluation Status Badge**:
    - "Submitted" (Green): `project.course_evaluations` has an entry for `user.id` with `submitted: true`.
    - "Draft" (Yellow): `submitted: false`.
    - "Not Started" (Gray): No entry found.
  - **Results Badge**: "Available" (Green) if `results_unlocked: true`, else "Pending" (Gray).
  - **Actions**: "Submit Evaluation" (if not submitted) and "View Results" (if unlocked).

### 3. Implement `src/pages/student/CourseEvaluation.tsx`

The multi-step evaluation form.

Requirements:
- **State Management**: Initialize from `getCourseEvaluation(projectId)` if it exists.
- **Star Rating**: Implement a 1-5 star selection for course rating.
- **Team Evaluations**: List all teammates (excluding self). Show their Name, Email (as `mailto:` link), and GitHub (using `<GitHubLogo />`).
- **Bonus Points**: Show the redistribution sliders ONLY if `course.peer_bonus_budget` is not null.
- **Accessibility**: 
  - Sliders must have `aria-label` (e.g., "Points for {name}").
  - Use `aria-live="polite"` for the "Remaining Points" counter.
- **Validation**: 
  - Ensure all textareas (strengths/improvements) are non-empty before submission.
  - Total bonus points must exactly match the budget.
- **Auto-save**: Support "Save Draft" (`submitted: false`) without strict validation.

### 4. Implement `src/pages/student/Results.tsx`

Shows the final verdict and feedback.

Requirements:
- **Lecturer Feedback**: Show averaged scores per criterion from `project.course.evaluation_criteria`. Display individual lecturer comments.
- **Peer Feedback**: Show feedback entries from `received_peer_feedback`.
- **Verdict**:
  - Calculate `Final Score = Average(Lecturer Scores) + Average(Peer Bonus)`.
  - Display "PASS" (Green) if `Final Score >= course.min_score`, else "FAIL" (Red).
- **Empty States**: Handle cases where some feedback might be missing gracefully.

## I18n Additions

Add these to `src/contexts/LanguageContext.tsx`:
```ts
'student.no_project': { cs: 'Nejste přiřazeni k žádnému projektu.', en: 'You are not assigned to any project.' }
'student.evaluation_status': { cs: 'Stav hodnocení', en: 'Evaluation Status' }
'student.results_status': { cs: 'Stav výsledků', en: 'Results Status' }
'student.submitted': { cs: 'Odesláno', en: 'Submitted' }
'student.draft': { cs: 'Koncept', en: 'Draft' }
'student.not_started': { cs: 'Nezahájeno', en: 'Not Started' }
'student.results_available': { cs: 'Dostupné', en: 'Available' }
'student.results_pending': { cs: 'Čeká se', en: 'Pending' }
'student.submit_evaluation': { cs: 'Odevzdat hodnocení', en: 'Submit Evaluation' }
'student.view_results': { cs: 'Zobrazit výsledky', en: 'View Results' }
'student.points_remaining': { cs: 'Zbývající body', en: 'Remaining Points' }
'student.anonymous_notice': { cs: 'Hodnocení je anonymní.', en: 'Evaluation is anonymous.' }
'results.total_score': { cs: 'Celkové skóre', en: 'Total Score' }
'results.verdict': { cs: 'Výsledek', en: 'Verdict' }
'results.pass': { cs: 'SPLNĚNO', en: 'PASS' }
'results.fail': { cs: 'NESPLNĚNO', en: 'FAIL' }
```

## Constraints

- **Testing**: Add colocated tests (`.test.tsx`) for:
  - `StudentHome`: Filtering and badge logic.
  - `usePointRedistribution`: Unit test for the math logic.
  - `CourseEvaluation`: Form submission and validation.
- **Visuals**: Maintain high-fidelity Tailwind styling (rounded-2xl, shadow-xl, consistent spacing).
- **Navigation**: Use `useNavigate` for post-submission redirects. Ensure the "Back" button always goes to `/student`.

## Validation

```bash
cd frontend
npm run build
npm run lint
npm test
```
Fix all errors.
