import '@testing-library/jest-dom/vitest';

// Provide a working in-memory localStorage implementation.
// jsdom 29 throws a SecurityError when the document URL has an opaque origin
// (the default `about:blank`), so we replace the built-in stub before any test
// code or component code tries to access it.
const createStorageMock = (): Storage => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string): string | null => store[key] ?? null,
    setItem: (key: string, value: string): void => { store[key] = String(value); },
    removeItem: (key: string): void => { delete store[key]; },
    clear: (): void => { store = {}; },
    get length(): number { return Object.keys(store).length; },
    key: (i: number): string | null => Object.keys(store)[i] ?? null,
  };
};

Object.defineProperty(globalThis, 'localStorage', {
  value: createStorageMock(),
  writable: true,
});

Object.defineProperty(globalThis, 'sessionStorage', {
  value: createStorageMock(),
  writable: true,
});
