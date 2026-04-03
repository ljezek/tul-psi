import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Login } from './Login';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { AuthProvider } from '@/contexts/AuthContext';
import * as api from '@/api';

// Mock the API module correctly to include ApiError
vi.mock('@/api', async (importOriginal) => {
  const actual = await importOriginal<typeof api>();
  return {
    ...actual,
    requestOtp: vi.fn(),
    verifyOtp: vi.fn(),
    getCurrentUser: vi.fn(),
  };
});

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: not authenticated
    (api.getCurrentUser as Mock).mockRejectedValue(new Error('Unauthorized'));
  });

  const renderLogin = async () => {
    let result;
    await act(async () => {
      result = render(
        <LanguageProvider>
          <AuthProvider>
            <MemoryRouter initialEntries={['/login']}>
              <Login />
            </MemoryRouter>
          </AuthProvider>
        </LanguageProvider>
      );
    });
    return result;
  };

  it('transitions from email step to OTP step on success', async () => {
    const user = userEvent.setup();
    (api.requestOtp as Mock).mockResolvedValue({ message: 'Success' });
    
    await renderLogin();
    
    const emailInput = screen.getByPlaceholderText('jan.novak');
    await user.type(emailInput, 'test.user');
    
    const submitButton = screen.getByRole('button', { name: /Odeslat kód/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(api.requestOtp).toHaveBeenCalledWith('test.user@tul.cz');
      expect(screen.getByText(/Jednorázový kód/i)).toBeInTheDocument();
      expect(screen.getByText('test.user@tul.cz')).toBeInTheDocument();
    });
  });

  it('shows validation error for empty email', async () => {
    await renderLogin();
    
    const submitButton = screen.getByRole('button', { name: /Odeslat kód/i });
    expect(submitButton).toBeDisabled();
  });

  it('supports pasting a 6-digit OTP code', async () => {
    const user = userEvent.setup();
    (api.requestOtp as Mock).mockResolvedValue({ message: 'Success' });
    
    await renderLogin();
    
    // Step 1
    await user.type(screen.getByPlaceholderText('jan.novak'), 'test.user');
    await user.click(screen.getByRole('button', { name: /Odeslat kód/i }));
    
    // Step 2
    await waitFor(() => screen.getByText(/Jednorázový kód/i));
    
    const firstDigitInput = screen.getByLabelText(/Číslice 1 z 6/i);
    
    // Simulate paste
    await act(async () => {
      fireEvent.paste(firstDigitInput, {
        clipboardData: {
          getData: () => '123456',
        },
      });
    });
    
    await waitFor(() => {
      expect(api.verifyOtp).toHaveBeenCalledWith('test.user@tul.cz', '123456');
    });
  });

  it('auto-submits when all 6 digits are manually typed', async () => {
    const user = userEvent.setup();
    (api.requestOtp as Mock).mockResolvedValue({ message: 'Success' });
    
    await renderLogin();
    
    await user.type(screen.getByPlaceholderText('jan.novak'), 'test.user');
    await user.click(screen.getByRole('button', { name: /Odeslat kód/i }));
    
    await waitFor(() => screen.getByText(/Jednorázový kód/i));
    
    const inputs = [
      screen.getByLabelText(/Číslice 1 z 6/i),
      screen.getByLabelText(/Číslice 2 z 6/i),
      screen.getByLabelText(/Číslice 3 z 6/i),
      screen.getByLabelText(/Číslice 4 z 6/i),
      screen.getByLabelText(/Číslice 5 z 6/i),
      screen.getByLabelText(/Číslice 6 z 6/i),
    ];
    
    for (let i = 0; i < 6; i++) {
      await user.type(inputs[i], (i + 1).toString());
    }
    
    await waitFor(() => {
      expect(api.verifyOtp).toHaveBeenCalledWith('test.user@tul.cz', '123456');
    });
  });

  it('displays error for invalid OTP (401)', async () => {
    const user = userEvent.setup();
    (api.requestOtp as Mock).mockResolvedValue({ message: 'Success' });
    
    const apiError = new api.ApiError(401, { detail: 'Invalid code' });
    (api.verifyOtp as Mock).mockRejectedValue(apiError);
    
    await renderLogin();
    
    await user.type(screen.getByPlaceholderText('jan.novak'), 'test.user');
    await user.click(screen.getByRole('button', { name: /Odeslat kód/i }));
    
    await waitFor(() => screen.getByText(/Jednorázový kód/i));
    
    const firstDigitInput = screen.getByLabelText(/Číslice 1 z 6/i);
    await act(async () => {
      fireEvent.paste(firstDigitInput, {
        clipboardData: { getData: () => '000000' },
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText(/Neplatný nebo expirovaný kód/i)).toBeInTheDocument();
    });
  });

  it('displays error for too many attempts (429)', async () => {
    const user = userEvent.setup();
    (api.requestOtp as Mock).mockResolvedValue({ message: 'Success' });
    
    const apiError = new api.ApiError(429, { detail: 'Too many attempts' });
    (api.verifyOtp as Mock).mockRejectedValue(apiError);
    
    await renderLogin();
    
    await user.type(screen.getByPlaceholderText('jan.novak'), 'test.user');
    await user.click(screen.getByRole('button', { name: /Odeslat kód/i }));
    
    await waitFor(() => screen.getByText(/Jednorázový kód/i));
    
    const firstDigitInput = screen.getByLabelText(/Číslice 1 z 6/i);
    await act(async () => {
      fireEvent.paste(firstDigitInput, {
        clipboardData: { getData: () => '000000' },
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText(/Příliš mnoho pokusů — vyžádejte nový kód/i)).toBeInTheDocument();
    });
  });
});
