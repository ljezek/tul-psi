# Prompt 7: Admin Panel — User Management, Course Editing, Admin Flows

You are continuing development of the React frontend in `frontend/`. Phases 1-6 are complete — the app has a solid foundation, dashboard, login, student zone, and lecturer panel.

## Context

- Routes `/admin/users` is protected by `ProtectedRoute` for ADMIN role.
- Lecturers and Admins can manage courses they are assigned to (or all for Admin) at `/lecturer/course/:id`.
- `@/api` needs expansion for admin-specific endpoints.
- Types: `UserPublic`, `UserCreate`, `AdminUserUpdate`, `CourseCreate`, `CourseUpdate`, `CourseDetail`.
- Use existing UI components: `Button`, `LoadingSpinner`, `ErrorMessage`, `Table`, `Modal`, `Switch/Toggle` (create if missing).

## Task

### 1. Update `src/api.ts`

Add these endpoints:
- `getUsers(): Promise<UserPublic[]>` — GET `/api/v1/users`
- `createUser(data: UserCreate): Promise<UserPublic>` — POST `/api/v1/users`
- `updateUser(id: number, data: AdminUserUpdate): Promise<UserPublic>` — PATCH `/api/v1/users/{id}`
- `createCourse(data: CourseCreate): Promise<CourseDetail>` — POST `/api/v1/courses`
- `updateCourse(id: number, data: CourseUpdate): Promise<CourseDetail>` — PATCH `/api/v1/courses/{id}`
- `lockProject(projectId: number): Promise<ProjectPublic>` — POST `/api/v1/projects/{id}/lock` (TODO: backend endpoint may need to be added; for now, assume it exists and handles setting `results_unlocked=False`).

### 2. Implement `src/pages/admin/UserManagement.tsx`

A new page for managing all users in the system.

Requirements:
- **Search & Filter**:
  - Search bar for name or email.
  - Dropdown to filter by role (ADMIN, LECTURER, STUDENT).
  - Toggle to show only inactive users.
- **User Table**:
  - Columns: Name, Email, Role (colored badge), Status (Active/Inactive badge).
  - Actions: 
    - "Edit" button → opens `UserForm` modal.
    - "Deactivate/Activate" toggle → calls `updateUser(id, { is_active: !current })`.
- **Add User**:
  - "Add User" button at the top → opens `UserForm` modal in "create" mode.
- **UserForm Modal**:
  - Fields: Email (required, @tul.cz), Name (required), GitHub Alias, Role (select), Active (checkbox).
  - Handles both Create and Update.

### 3. Implement Course Creation & Editing

Extend the course management capabilities.

Requirements:
- **Admin Home Extension**:
  - In `LecturerHome.tsx` (or a dedicated `AdminHome`), if the user is an ADMIN, show an "Add Course" button.
  - "Add Course" opens a `CourseForm` modal or navigates to a creation page.
- **Course Settings**:
  - In `CourseProjects.tsx`, add a "Settings" tab or a "Edit Course" button (visible to Admins and assigned Lecturers).
  - This should render a `CourseForm`.
- **CourseForm Component**:
  - **Basic Info**: Code (unique), Name, Term (SUMMER/WINTER), Project Type (TEAM/INDIVIDUAL), Min Score.
  - **Syllabus**: Textarea.
  - **Peer Bonus**: Number input for `peer_bonus_budget` (nullable).
  - **Evaluation Criteria**: Dynamic list where you can add/remove criteria. Each criterion has: Code, Description, Max Score.
  - **Links**: Dynamic list for course links (Label, URL).
  - **Lecturers**: Section to add/remove lecturers by email (using `addCourseLecturer` and `removeCourseLecturer` API calls).

### 4. Admin "Relock" Flow

Unblock stuck lecturers or fix accidental unlocks.

Requirements:
- In `CourseProjects.tsx` or `ProjectDetail.tsx`, if user is an ADMIN and `project.results_unlocked` is `true`:
  - Show a "Relock Results" button (red outline or ghost variant).
  - Clicking shows a confirmation dialog: "This will hide results from students and allow lecturers to edit evaluations again. Continue?"
  - On confirm, call `lockProject(projectId)` and refresh the data.

### 5. Update Router in `src/App.tsx`

Add the new admin routes:
```tsx
<Route element={<ProtectedRoute allowedRoles={[UserRole.ADMIN]} />}>
  <Route path="/admin/users" element={<UserManagement />} />
</Route>
```
Update `MainLayout.tsx` to show "User Management" link in the nav for ADMIN users.

## I18n Additions

Add these to `src/contexts/LanguageContext.tsx`:
```ts
'admin.user_management': { cs: 'Správa uživatelů', en: 'User Management' }
'admin.add_user': { cs: 'Přidat uživatele', en: 'Add User' }
'admin.edit_user': { cs: 'Upravit uživatele', en: 'Edit User' }
'admin.role': { cs: 'Role', en: 'Role' }
'admin.status': { cs: 'Stav', en: 'Status' }
'admin.active': { cs: 'Aktivní', en: 'Active' }
'admin.inactive': { cs: 'Neaktivní', en: 'Inactive' }
'admin.create_course': { cs: 'Vytvořit kurz', en: 'Create Course' }
'admin.edit_course': { cs: 'Upravit kurz', en: 'Edit Course' }
'admin.relock_results': { cs: 'Znovu uzamknout výsledky', en: 'Relock Results' }
'admin.confirm_relock': { cs: 'Opravdu chcete výsledky znovu uzamknout?', en: 'Are you sure you want to relock results?' }
'course.criteria': { cs: 'Kritéria hodnocení', en: 'Evaluation Criteria' }
'course.links': { cs: 'Odkazy', en: 'Links' }
'course.add_criterion': { cs: 'Přidat kritérium', en: 'Add Criterion' }
'course.add_link': { cs: 'Přidat odkaz', en: 'Add Link' }
```

## Constraints

- **Reusability**: Try to reuse `UserPublic`, `CourseDetail` etc. from existing types.
- **Validation**: Ensure `min_score` is non-negative, `max_score` for criteria is positive.
- **Visuals**: Consistent with TUL blue branding and existing cards/tables.
- **Error Handling**: Show specific errors for duplicate course codes or invalid emails.

## Validation

```bash
cd frontend
npm run build
npm run lint
npm test
```
Fix all errors.
