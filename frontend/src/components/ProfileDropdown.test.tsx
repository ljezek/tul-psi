import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProfileDropdown } from './ProfileDropdown';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { AuthProvider } from '@/contexts/AuthContext';
import * as api from '@/api';
import { UserRole } from '@/types';

// Mock the API module correctly
vi.mock('@/api', async (importOriginal) => {
  const actual = await importOriginal<typeof api>();
  return {
    ...actual,
    getCurrentUser: vi.fn(),
    updateCurrentUser: vi.fn(),
  };
});

const mockUser = {
  id: 1,
  email: 'test@tul.cz',
  name: 'Test User',
  github_alias: 'testuser',
  role: UserRole.STUDENT,
  is_active: true,
};

describe('ProfileDropdown', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getCurrentUser as Mock).mockResolvedValue(mockUser);
  });

  const renderDropdown = async () => {
    let result;
    await act(async () => {
      result = render(
        <LanguageProvider>
          <AuthProvider>
            <ProfileDropdown />
          </AuthProvider>
        </LanguageProvider>
      );
    });
    return result;
  };

  it('renders user name and opens dropdown on click', async () => {
    const user = userEvent.setup();
    await renderDropdown();
    
    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });
    
    const trigger = screen.getByRole('button', { name: /Test User/i });
    await user.click(trigger);
    
    expect(screen.getByText(/Upravit profil/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
    expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
  });

  it('submits profile changes correctly', async () => {
    const user = userEvent.setup();
    (api.updateCurrentUser as Mock).mockResolvedValue({ ...mockUser, name: 'New Name' });
    
    await renderDropdown();
    await waitFor(() => screen.getByText('Test User'));
    
    await user.click(screen.getByRole('button', { name: /Test User/i }));
    
    const nameInput = screen.getByLabelText(/Jméno/i);
    await user.clear(nameInput);
    await user.type(nameInput, 'New Name');
    
    const saveButton = screen.getByRole('button', { name: /Uložit změny/i });
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(api.updateCurrentUser).toHaveBeenCalledWith({
        name: 'New Name',
        github_alias: 'testuser',
      });
      expect(screen.getByText(/Profil byl úspěšně aktualizován/i)).toBeInTheDocument();
    });
  });

  it('handles API errors during update', async () => {
    const user = userEvent.setup();
    (api.updateCurrentUser as Mock).mockRejectedValue(new Error('Update failed'));
    
    await renderDropdown();
    await waitFor(() => screen.getByText('Test User'));
    
    await user.click(screen.getByRole('button', { name: /Test User/i }));
    
    const saveButton = screen.getByRole('button', { name: /Uložit změny/i });
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Nepodařilo se aktualizovat profil/i)).toBeInTheDocument();
    });
  });

  it('closes dropdown when clicking the close button', async () => {
    const user = userEvent.setup();
    await renderDropdown();
    await waitFor(() => screen.getByText('Test User'));
    
    const trigger = screen.getByRole('button', { name: /Test User/i });
    await user.click(trigger);
    expect(screen.getByText(/Upravit profil/i)).toBeInTheDocument();
    
    // Find the close button (X icon) - it's the second button in the dropdown header usually
    const closeButton = screen.getByRole('button', { name: '' });
    await user.click(closeButton);
    
    expect(screen.queryByText(/Upravit profil/i)).not.toBeInTheDocument();
  });
});
