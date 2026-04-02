# Prompt 6: Polish & Tests — Error Fixing, Component Tests, Final Cleanup

You are completing the React frontend in `frontend/`. All 5 phases are done — the app has a working dashboard, project browser/detail, OTP login, student zone (evaluation form + results), and lecturer panel (course management + project evaluation).

## Context

- Test infrastructure: Vitest 3 + React Testing Library + jsdom. Config in `vite.config.ts` and `vitest.setup.ts`.
- Test conventions from `.github/copilot-instructions.md`:
  - Tests colocated with components: `Component.test.tsx` next to `Component.tsx`.
  - Use `describe()` + `it()` (not `test()`).
  - Query priority: `getByRole` > `getByLabelText` > `getByTestId` (last resort).
  - Always wrap in required providers (LanguageProvider, etc.).
  - Use `userEvent` (not `fireEvent`).
  - Assert on user-visible outcomes.
- Existing tests: `src/contexts/LanguageContext.test.tsx` (ported from prototype), `src/App.test.tsx` (updated in Phase 1).
- `@/api` module can be mocked with `vi.mock('@/api', ...)` for component tests.
- `@/contexts/AuthContext` can be mocked or wrapped with a test provider.

## Task

### 1. Fix all build and lint issues

Run these commands and fix ALL errors:
```bash
cd frontend
npm run build
npm run lint
npm test
```

Common issues to look for:
- Unused imports (remove them or prefix with `_`).
- Missing translation keys (add to LanguageContext).
- Type mismatches between API responses and component expectations.
- Missing `key` props in lists.
- React Router v6 API issues.
- Import path issues (should use `@/` aliases).

### 2. Write component tests for critical logic

Add Vitest tests for the following components. Each test file sits next to its component.

**`src/api.test.ts`** — Test the API client:
- Mock `fetch` globally with `vi.fn()`.
- Test `apiFetch` sets correct headers, credentials, and throws `ApiError` on non-2xx.
- Test `getProjects` builds query string correctly.
- Test `requestOtp` sends correct body.

**`src/contexts/AuthContext.test.tsx`** — Test auth context:
- Mock `@/api` module.
- Test: mounts, calls `getCurrentUser`, sets user on success.
- Test: mounts, calls `getCurrentUser`, sets user to null on 401.
- Test: `login()` calls `verifyOtp` then `getCurrentUser`.
- Test: `logout()` clears user state.
- Wrap test components in `LanguageProvider` if needed.

**`src/pages/Dashboard.test.tsx`** — Test dashboard:
- Mock `@/api` to return fake projects and courses.
- Test: renders project cards for fetched data.
- Test: filters projects by search text.
- Test: shows empty state when no results match filter.
- Wrap in necessary providers (LanguageProvider, MemoryRouter, AuthProvider or mock).

**`src/components/ProjectCard.test.tsx`** — Test project card:
- Test: renders project title, course code, technologies.
- Test: renders GitHub link when github_url is present.
- Test: does not render GitHub link when github_url is null.
- Wrap in LanguageProvider and MemoryRouter.

**`src/pages/Login.test.tsx`** — Test login page:
- Mock `@/api` and auth context.
- Test: renders email input initially.
- Test: shows error for non-@tul.cz email.
- Test: transitions to OTP step after successful requestOtp.
- Wrap in necessary providers.

### 3. Review and add missing i18n keys

Go through all components and ensure every user-visible string uses the `t()` function. Check for:
- Button labels
- Error messages
- Placeholder text
- Status badges
- Section headings
- Empty state messages

Add any missing keys to `src/contexts/LanguageContext.tsx`.

### 4. Add TODO comments for tech debt

Ensure these TODOs exist somewhere in the codebase (add to relevant files if not already present):
- `// TODO: Migrate to React Query for data fetching with caching and deduplication.`
- `// TODO: Add MSW (Mock Service Worker) for more realistic API mocking in tests.`
- `// TODO: Add @opentelemetry/sdk-web for frontend RUM traces.`
- `// TODO: Build AdminPanel for user/course management (admin role).`
- `// TODO: Add Playwright E2E test suites.`
- `// TODO: Implement XSRF Double Submit Cookie pattern for CSRF protection.`
- `// TODO: Add backend logout endpoint to invalidate JWT server-side.`
- `// TODO: Add profile editing (name, github_alias) via PATCH /users/me.`
- `// TODO: Add course list page.`
- `// TODO: Add evaluation overview table for lecturers.`
- `// TODO: Add image/thumbnail support for project cards.`

### 5. Final accessibility check

Quick pass over the main components to ensure:
- All `<img>` tags have `alt` attributes.
- Form inputs have associated `<label>` elements (or `aria-label`).
- Buttons have accessible text (visible text or `aria-label`).
- Links have descriptive text.
- Color contrast is reasonable (tul-blue on white, slate-800 on white are fine).

### 6. Verify the complete app

Run the full validation suite:
```bash
cd frontend
npm run build    # Must succeed with no errors
npm run lint     # Must succeed with no errors (warnings OK)
npm test         # All tests must pass
```

Then do a quick manual sanity check — describe what the first page renders and confirm the router works.

## Constraints

- Do not add features beyond what's in the plan.
- Do not refactor working code — just fix issues and add tests.
- Keep tests focused on critical logic, avoid trivial tests.
- All test files colocated with their component.

## Output

After completing all tasks, provide:
1. List of all files created or modified.
2. Output of `npm run build`, `npm run lint`, `npm test`.
3. Summary of any remaining known issues or TODOs.
