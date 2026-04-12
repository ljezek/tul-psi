import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { UserManagement } from './UserManagement';
import { LanguageProvider } from '@/contexts/LanguageContext';
import * as api from '@/api';
import { UserRole, UserPublic } from '@/types';

vi.mock('@/api', () => ({
  getUsers: vi.fn(),
  createUser: vi.fn(),
  updateUser: vi.fn(),
  ApiError: class extends Error {
    status: number;
    detail: unknown;
    constructor(status: number, detail: unknown) {
      super();
      this.status = status;
      this.detail = detail;
    }
  }
}));

const mockUsers: UserPublic[] = [
  { id: 1, name: 'Admin User', email: 'admin@tul.cz', role: UserRole.ADMIN, is_active: true, github_alias: 'admin' },
  { id: 2, name: 'Student One', email: 'student1@tul.cz', role: UserRole.STUDENT, is_active: true, github_alias: null },
  { id: 3, name: 'Inactive Lecturer', email: 'lecturer@tul.cz', role: UserRole.LECTURER, is_active: false, github_alias: 'lecturer' },
];

const renderUserManagement = () => {
  return render(
    <LanguageProvider>
      <MemoryRouter>
        <UserManagement />
      </MemoryRouter>
    </LanguageProvider>
  );
};

describe('UserManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getUsers as ReturnType<typeof vi.fn>).mockResolvedValue(mockUsers);
  });

  it('renders user list and handles search', async () => {
    renderUserManagement();

    await waitFor(() => {
      expect(screen.getByText('Admin User')).toBeInTheDocument();
      expect(screen.getByText('Student One')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/hledat/i);
    await userEvent.type(searchInput, 'Student');

    expect(screen.getByText('Student One')).toBeInTheDocument();
    expect(screen.queryByText('Admin User')).not.toBeInTheDocument();
  });

  it('filters users by role', async () => {
    renderUserManagement();

    await waitFor(() => screen.getByText('Admin User'));

    const roleSelect = screen.getByRole('combobox');
    await userEvent.selectOptions(roleSelect, UserRole.ADMIN);

    expect(screen.getByText('Admin User')).toBeInTheDocument();
    expect(screen.queryByText('Student One')).not.toBeInTheDocument();
  });

  it('opens add user modal and submits data', async () => {
    renderUserManagement();
    await waitFor(() => screen.getByText('Admin User'));

    const addButton = screen.getByText(/přidat uživatele/i);
    await userEvent.click(addButton);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    
    // Type name first
    await userEvent.type(screen.getByLabelText(/^jméno$/i), 'Jan Novak');
    // Email should be auto-filled by handleNameChange
    expect(screen.getByLabelText(/univerzitní email/i)).toHaveValue('jan.novak');

    await userEvent.selectOptions(screen.getByLabelText(/^role$/i), UserRole.LECTURER);

    const submitButton = screen.getByRole('button', { name: /^přidat$/i });
    await userEvent.click(submitButton);

    expect(api.createUser).toHaveBeenCalledWith(expect.objectContaining({
      email: 'jan.novak@tul.cz',
      name: 'Jan Novak',
      role: UserRole.LECTURER
    }));
  });

  it('submits null name if empty', async () => {
    renderUserManagement();
    await waitFor(() => screen.getByText('Admin User'));

    const addButton = screen.getByText(/přidat uživatele/i);
    await userEvent.click(addButton);

    await userEvent.type(screen.getByLabelText(/univerzitní email/i), 'noname');
    
    const submitButton = screen.getByRole('button', { name: /^přidat$/i });
    await userEvent.click(submitButton);

    expect(api.createUser).toHaveBeenCalledWith(expect.objectContaining({
      email: 'noname@tul.cz',
      name: null
    }));
  });

  it('toggles user status', async () => {
    renderUserManagement();
    await waitFor(() => screen.getByText('Admin User'));

    // Select specifically the status toggle in the table, not the filter toggle
    const statusButtons = screen.getAllByText(/aktivní/i);
    const userStatusButton = statusButtons.find(el => el.tagName === 'BUTTON');
    if (!userStatusButton) throw new Error('Status button not found');
    
    await userEvent.click(userStatusButton);

    expect(api.updateUser).toHaveBeenCalledWith(1, { is_active: false });
  });
});
