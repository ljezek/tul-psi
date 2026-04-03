# Prompt 3: Authentication Flow — Login Page, Profile in Nav

You are continuing development of the React frontend in `frontend/`. Phases 1-2 are complete — the app has working types, API client, contexts, router, layout, dashboard with project cards, and project detail page.

## Context

- `@/api` exports: `requestOtp(email)`, `verifyOtp(email, otp)`, `getCurrentUser()`, `updateCurrentUser(data)`.
- `@/contexts/AuthContext` exports `useAuth()` with: `user`, `loading`, `login(email, otp)`, `logout()`, `refreshUser()`.
- `@/components/ui/Button` with variants: primary/secondary/outline/ghost, sizes: sm/md/lg.
- `@/components/ui/LoadingSpinner` and `@/components/ui/ErrorMessage` exist.
- Backend OTP flow: `POST /api/v1/auth/otp/request { email }` → always returns 200 with `{ message: "..." }`. `POST /api/v1/auth/otp/verify { email, otp }` → 200 + sets HttpOnly session cookie, 401 for invalid/expired, 429 for too many attempts, 422 for bad email. Only `@tul.cz` emails accepted (422 from Pydantic validation if not).
- `@/contexts/LanguageContext` has `t()` for i18n.

## Task

### 1. Implement `src/pages/Login.tsx`

Replace the placeholder with a two-step OTP login form.

Requirements:
- **If already authenticated** (from `useAuth()`): redirect to role-appropriate route using `Navigate`:
  - STUDENT → `/student`
  - LECTURER or ADMIN → `/lecturer`
- **Step 1 — Email**: 
  - Input field for email address, label: `t('login.email_label')` or similar.
  - Client-side validation: must end with `@tul.cz`. Show inline error if not.
  - Submit button: "Send Code" / `t('login.send_code')`.
  - On submit: call `requestOtp(email)`. Show loading state on button. On success, transition to step 2. On 422 error, show "Invalid email" message.
  - Info text: "Enter your @tul.cz email address to receive a one-time login code."
- **Step 2 — OTP**:
  - Show which email the code was sent to.
  - Input field for 6-digit code (text input, maxLength 6).
  - Submit button: "Verify" / `t('login.verify')`.
  - On submit: call `login(email, otp)` from auth context (which calls verifyOtp + refreshUser).
  - On success: navigate to role-appropriate route (same logic as above) using `useNavigate()`.
  - On 401 error: show "Invalid or expired code" message.
  - On 429 error: show "Too many attempts — request a new code" message.
  - "Back" link to go back to email step.
  - "Resend code" action that calls `requestOtp(email)` again.
- **Design**: centered card (max-w-md mx-auto), white bg, rounded-xl, shadow-lg, padding. TUL branding at top (the FM logo + title). Use `lucide-react` `Mail` and `KeyRound` icons.
- Error messages shown as red text below the relevant input.
- All button states: default, loading (disabled + spinner), disabled.

Add these translation keys to `src/contexts/LanguageContext.tsx`:
```
'login.title': { cs: 'Přihlášení', en: 'Login' }
'login.email_label': { cs: 'Univerzitní email', en: 'University Email' }
'login.email_placeholder': { cs: 'jan.novak@tul.cz', en: 'jan.novak@tul.cz' }
'login.send_code': { cs: 'Odeslat kód', en: 'Send Code' }
'login.email_info': { cs: 'Zadejte svůj @tul.cz email pro přihlášení.', en: 'Enter your @tul.cz email to sign in.' }
'login.code_sent': { cs: 'Kód byl odeslán na', en: 'Code sent to' }
'login.otp_label': { cs: 'Jednorázový kód', en: 'One-Time Code' }
'login.otp_placeholder': { cs: '123456', en: '123456' }
'login.verify': { cs: 'Ověřit', en: 'Verify' }
'login.back': { cs: 'Zpět', en: 'Back' }
'login.resend': { cs: 'Odeslat znovu', en: 'Resend Code' }
'login.error_invalid_email': { cs: 'Zadejte platný @tul.cz email.', en: 'Enter a valid @tul.cz email.' }
'login.error_invalid_otp': { cs: 'Neplatný nebo expirovaný kód.', en: 'Invalid or expired code.' }
'login.error_too_many': { cs: 'Příliš mnoho pokusů — vyžádejte nový kód.', en: 'Too many attempts — request a new code.' }
```

### 2. Update `src/layouts/MainLayout.tsx` — Auth section in nav

The nav bar should now show:
- **Unauthenticated**: a "Login" link/button in the nav bar, navigating to `/login`. Use `LogIn` icon.
- **Authenticated**: 
  - User's name displayed.
  - Role badge (small colored pill): STUDENT = purple bg, LECTURER = tul-blue bg, ADMIN = slate-800 bg.
  - "Logout" button/icon button. On click: call `logout()` from auth context, then navigate to `/`.
  - Use `LogOut` icon from lucide-react.
- The mobile hamburger menu should include the same auth items.

### 3. Profile editing

Add an inline profile edit capability:
- Clicking the user name in the nav opens a small dropdown/modal.
- Shows name (editable input) and github_alias (editable input).
- Save button calls `updateCurrentUser({ name, github_alias })`, then `refreshUser()`.

## Constraints

- Use `@/*` import aliases.
- No `React` import needed.
- All user-visible strings through `t()`.
- No `any` types.
- Handle all error states from the API gracefully.

## Validation

```bash
cd frontend
npm run build
npm run lint
npm test
```
Fix all errors.
