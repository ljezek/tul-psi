/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APPINSIGHTS_CONNECTION_STRING: string;
  readonly VITE_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
