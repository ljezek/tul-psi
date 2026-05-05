import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext';

// A minimal component that exposes the context value for assertions.
const TestComponent = () => {
  const { theme, toggleTheme } = useTheme();
  return (
    <div>
      <p data-testid="current-theme">{theme}</p>
      <button onClick={toggleTheme}>Toggle Theme</button>
    </div>
  );
};

describe('ThemeContext', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  afterEach(() => {
    document.documentElement.classList.remove('dark');
  });

  describe('Theme initialization', () => {
    it('defaults to light theme when no saved preference exists', () => {
      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('current-theme')).toHaveTextContent('light');
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });

    it('restores dark theme from localStorage on mount', () => {
      localStorage.setItem('theme', 'dark');

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('current-theme')).toHaveTextContent('dark');
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('applies the dark class synchronously during initialization', () => {
      localStorage.setItem('theme', 'dark');

      // The dark class must be present before the component tree renders so
      // the initial paint already uses the correct palette (no flash).
      let classAppliedBeforeRender = false;
      const SpyComponent = () => {
        classAppliedBeforeRender = document.documentElement.classList.contains('dark');
        return <div />;
      };

      render(
        <ThemeProvider>
          <SpyComponent />
        </ThemeProvider>
      );

      expect(classAppliedBeforeRender).toBe(true);
    });
  });

  describe('Theme toggling', () => {
    it('toggles from light to dark and adds the root dark class', async () => {
      const user = userEvent.setup();
      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('current-theme')).toHaveTextContent('light');

      await act(async () => {
        await user.click(screen.getByRole('button', { name: /toggle theme/i }));
      });

      expect(screen.getByTestId('current-theme')).toHaveTextContent('dark');
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('toggles from dark back to light and removes the root dark class', async () => {
      localStorage.setItem('theme', 'dark');
      const user = userEvent.setup();
      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await act(async () => {
        await user.click(screen.getByRole('button', { name: /toggle theme/i }));
      });

      expect(screen.getByTestId('current-theme')).toHaveTextContent('light');
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });

    it('persists the new theme in localStorage after toggle', async () => {
      const user = userEvent.setup();
      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await act(async () => {
        await user.click(screen.getByRole('button', { name: /toggle theme/i }));
      });

      expect(localStorage.getItem('theme')).toBe('dark');
    });
  });

  describe('useTheme hook', () => {
    it('throws an error when used outside ThemeProvider', () => {
      const InvalidComponent = () => {
        useTheme();
        return <div>Test</div>;
      };

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<InvalidComponent />);
      }).toThrow('useTheme must be used within a ThemeProvider');

      consoleSpy.mockRestore();
    });
  });
});
