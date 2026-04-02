# Prompt 2: Public Views — Dashboard, ProjectCard, ProjectDetail

You are continuing development of the React frontend in `frontend/`. Phase 1 (Foundation) is complete — types, API client, auth context, language context, router, layout, and UI components are all in place.

## Context

- The app uses `react-router-dom` for routing, `@/api` for API calls, `@/contexts/AuthContext` for auth, `@/contexts/LanguageContext` for i18n.
- `@/types` has all TypeScript types matching the backend schemas (snake_case).
- `@/components/ui/Button` has variants: primary/secondary/outline/ghost.
- `@/components/ui/LoadingSpinner` and `@/components/ui/ErrorMessage` exist.
- The backend API base URL is in `@/config` as `config.apiUrl`.
- Read `prototype/components/Dashboard.tsx`, `prototype/components/ProjectCard.tsx`, and `prototype/components/ProjectModal.tsx` for UI reference. Do NOT modify prototype files.
- Backend endpoints: `GET /api/v1/projects` (with query params: q, course, year, term, technology), `GET /api/v1/projects/{id}`, `GET /api/v1/courses` (returns CourseListItem[]).

## Task

### 1. Implement `src/pages/Dashboard.tsx`

Replace the placeholder with the full project browser. Reference `prototype/components/Dashboard.tsx` for design.

Requirements:
- On mount, fetch projects (`getProjects()`) and courses (`getCourses()`) from the API.
- Show loading spinner while fetching. Show error message with retry on failure.
- **Search bar**: text input. On change, re-fetch projects with `q` filter param (debounce ~300ms with a `setTimeout` pattern, or send on enter — your choice, just don't hammer the API). Alternatively, fetch all projects once and filter client-side with `useMemo` for faster UX — this is preferred if the dataset is small (< 500 projects).
- **Filter bar**: 
  - Course dropdown populated from the courses list (show `code - name`). Filters by `course` code.
  - Academic year dropdown extracted from projects data (distinct years, sorted descending). Filters by `year`.
  - Technology filter: either a dropdown from all distinct technologies across projects, or a text input.
- Use `useMemo` for client-side filtering: combine search text, selected course, selected year, and selected technology to filter the projects array.
- **Grid layout**: responsive — 1 column on mobile, 2 on md, 3 on lg. Use `gap-6`.
- **No results state**: centered message with a search icon when filtered results are empty.
- Pass each project to `ProjectCard` component.
- i18n: use `t()` for all labels (dashboard.title, dashboard.subtitle, dashboard.search_placeholder, dashboard.filter_subject, dashboard.filter_year, dashboard.all_subjects, dashboard.all_years, dashboard.no_results, dashboard.try_adjust).
- Add a header section with title and subtitle above the filters.

### 2. Implement `src/components/ProjectCard.tsx`

Reference `prototype/components/ProjectCard.tsx` for design.

Props interface `ProjectCardProps`:
- `project: ProjectPublic`

Requirements:
- Card with white bg, rounded-xl, shadow-sm, hover:shadow-md transition.
- **Header area**: course code badge (bg-tul-blue/10 text-tul-blue) + academic year badge (top right, bg-slate-100).
- **Title**: project title as `h3`, hover color change to tul-blue.
- **Description**: `line-clamp-3` (truncated to 3 lines). Use `description` field, show placeholder if null.
- **Technologies**: row of small pills (bg-slate-100, text-xs, rounded-full, px-2 py-0.5). Show first 5, then "+N" if more.
- **Footer**: team member names (show last names, truncated if > 3 members, or first names). On the right side: GitHub icon link (if github_url) and external link icon (if live_url). Links open in new tab with `target="_blank" rel="noopener noreferrer"`. Stop click propagation on links.
- **Click handler**: entire card is clickable, navigates to `/projects/${project.id}` using `useNavigate()`.
- Use `lucide-react` icons: `Github`, `ExternalLink`, `Users`, `Tag`.

### 3. Implement `src/pages/ProjectDetail.tsx`

Replace the placeholder. This is a full page, NOT a modal. Reference `prototype/components/ProjectModal.tsx` for content layout.

Requirements:
- Read project ID from URL params (`useParams()`) and fetch `getProject(id)` on mount.
- Loading and error states.
- **Back link**: "← Back to projects" link at the top, navigates to `/`.
- **Header**: course code badge + course name, academic year, project title as `h1`.
- **Content** (two-column on desktop, stacked on mobile):
  - **Main column** (2/3):
    - Full description (or "No description provided" placeholder).
    - Technologies as pills.
    - Links section: GitHub button (outline variant) and Live Demo button (primary variant) when URLs exist.
  - **Sidebar** (1/3):
    - Team section: `t('project.team')` heading. List each member: name, github alias (as link to github.com/alias if present). Show email only if non-null (authenticated view).
    - Course info: course name, term, project type.
    - If authenticated as a project member (student): link to `/student/project/${id}/evaluate` and `/student/project/${id}/results` (if results_unlocked).
    - If authenticated as lecturer/admin: link to `/lecturer/project/${id}/evaluate`.
- Use `lucide-react` icons: `ArrowLeft`, `Github`, `ExternalLink`, `Users`, `BookOpen`, `Calendar`.

## Constraints

- Use `@/*` import aliases for all internal imports.
- No `React` import needed.
- All user-visible strings through `t()`. Add new translation keys to `LanguageContext.tsx` if needed.
- No `any` types.
- Add `// TODO:` comments for: image support (prototype has imageUrl but backend doesn't), and any other skipped features.

## Validation

```bash
cd frontend
npm run build
npm run lint
npm test
```
Fix all errors.
