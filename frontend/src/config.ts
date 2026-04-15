/**
 * Application configuration loaded from environment variables.
 * Copy .env.example to .env and adjust values for your local setup.
 */
export const config = {
  /** Base URL of the backend REST API */
  apiUrl: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  /** Logic App URL for submitting feedback */
  logicAppFeedbackUrl: import.meta.env.VITE_LOGIC_APP_FEEDBACK_URL ?? '',
} as const;
