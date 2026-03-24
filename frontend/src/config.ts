/**
 * Application configuration loaded from environment variables.
 * Copy .env.example to .env and adjust values for your local setup.
 */
export const config = {
  /** Base URL of the backend REST API */
  apiUrl: import.meta.env.VITE_API_URL ?? 'http://localhost:3001',
} as const;
