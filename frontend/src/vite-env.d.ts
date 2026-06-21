/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APPINSIGHTS_CONNECTION_STRING: string;
  readonly VITE_API_URL: string;
  /** Deployment environment: 'local' | 'e2e' | 'dev' | 'prod'. Omit for production. */
  readonly VITE_APP_ENV?: string;
  /** CSRF cookie name to read; defaults to 'XSRF-TOKEN'. Set per-env to avoid clashes. */
  readonly VITE_XSRF_COOKIE_NAME?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
