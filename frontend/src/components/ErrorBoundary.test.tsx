import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ErrorBoundary } from './ErrorBoundary';
import { LanguageProvider } from '@/contexts/LanguageContext';

// A component that throws a render-time error for testing the error boundary.
function ThrowingComponent({ message }: { message: string }): never {
  throw new Error(message);
}

// Suppress console.error output produced by React's error boundary mechanism
// so the test output stays clean (these are expected errors in these tests).
beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => undefined);
});

afterEach(() => {
  vi.restoreAllMocks();
});

const renderWithBoundary = (children: React.ReactNode) =>
  render(
    <LanguageProvider>
      <ErrorBoundary>{children}</ErrorBoundary>
    </LanguageProvider>
  );

describe('ErrorBoundary', () => {
  it('renders children when there is no error', () => {
    renderWithBoundary(<span>All good</span>);
    expect(screen.getByText('All good')).toBeInTheDocument();
  });

  it('renders the translated fallback heading when a child throws', () => {
    renderWithBoundary(<ThrowingComponent message="boom" />);
    // Czech is the default language — 'error.unexpected_title' = 'Něco se pokazilo'.
    expect(screen.getByRole('heading', { name: 'Něco se pokazilo' })).toBeInTheDocument();
  });

  it('renders the translated fallback description when a child throws', () => {
    renderWithBoundary(<ThrowingComponent message="boom" />);
    expect(
      screen.getByText('Nastala neočekávaná chyba. Zkuste stránku načíst znovu.')
    ).toBeInTheDocument();
  });

  it('renders a reload button in the fallback UI', () => {
    renderWithBoundary(<ThrowingComponent message="boom" />);
    // Czech label for 'error.reload' = 'Načíst stránku znovu'.
    expect(screen.getByRole('button', { name: 'Načíst stránku znovu' })).toBeInTheDocument();
  });

  it('clicking the reload button calls window.location.reload', async () => {
    const user = userEvent.setup();
    const reloadMock = vi.fn();
    vi.spyOn(window, 'location', 'get').mockReturnValue({
      ...window.location,
      reload: reloadMock,
    });

    renderWithBoundary(<ThrowingComponent message="boom" />);
    await user.click(screen.getByRole('button', { name: 'Načíst stránku znovu' }));
    expect(reloadMock).toHaveBeenCalledOnce();
  });

  it('shows error message in the development environment', () => {
    // Vitest always runs with import.meta.env.DEV = true, so the <pre> block
    // that reveals the raw error message should be present.
    renderWithBoundary(<ThrowingComponent message="secret internal detail" />);
    expect(screen.getByText('secret internal detail')).toBeInTheDocument();
  });

  it('hides error message in production mode', () => {
    // Temporarily set import.meta.env.DEV to false to simulate a production build.
    const origDev = import.meta.env.DEV;
    (import.meta.env as Record<string, unknown>).DEV = false;
    try {
      renderWithBoundary(<ThrowingComponent message="secret production detail" />);
      expect(screen.queryByText('secret production detail')).not.toBeInTheDocument();
    } finally {
      (import.meta.env as Record<string, unknown>).DEV = origDev;
    }
  });
});
