import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import App from './App';

describe('App', () => {
  beforeEach(() => {
    // Mock global fetch
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/users/me')) {
        return Promise.resolve({
          ok: false,
          status: 401,
          json: () => Promise.resolve({ detail: 'Not authenticated' }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    }));
  });

  it('renders the app with layout and dashboard route', async () => {
    render(<App />);
    
    // Wait for the AuthProvider to finish loading (fetchUser completes)
    await waitFor(() => {
      // The heading from Dashboard should appear ("Prohlížeč projektů" which is 'dashboard.title' in cs)
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Prohlížeč projektů');
    });

    // Subtitle from footer
    expect(screen.getByText(/Technická univerzita v Liberci/i)).toBeInTheDocument();
    
    // App title in nav
    expect(screen.getByText('Katalog Projektů')).toBeInTheDocument();
  });
});
