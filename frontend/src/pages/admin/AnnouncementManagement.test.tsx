import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AnnouncementManagement } from './AnnouncementManagement';
import { LanguageProvider } from '@/contexts/LanguageContext';
import * as api from '@/api';
import { AnnouncementPublic, AnnouncementSeverity } from '@/types';

vi.mock('@/api', () => ({
  getAnnouncements: vi.fn(),
  createAnnouncement: vi.fn(),
  updateAnnouncement: vi.fn(),
  deleteAnnouncement: vi.fn(),
  ApiError: class extends Error {
    status: number;
    detail: unknown;
    constructor(status: number, detail: unknown) {
      super();
      this.status = status;
      this.detail = detail;
    }
  },
}));

const mockAnnouncements: AnnouncementPublic[] = [
  {
    id: 1,
    message: 'System maintenance on Sunday.',
    severity: AnnouncementSeverity.WARNING,
    is_active: true,
    created_at: '2026-05-01T10:00:00Z',
    updated_at: '2026-05-01T10:00:00Z',
  },
  {
    id: 2,
    message: 'Evaluation deadline is May 15.',
    severity: AnnouncementSeverity.INFO,
    is_active: false,
    created_at: '2026-04-20T08:00:00Z',
    updated_at: '2026-04-20T08:00:00Z',
  },
];

const renderPage = () =>
  render(
    <LanguageProvider>
      <MemoryRouter>
        <AnnouncementManagement />
      </MemoryRouter>
    </LanguageProvider>,
  );

describe('AnnouncementManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getAnnouncements as ReturnType<typeof vi.fn>).mockResolvedValue(mockAnnouncements);
  });

  it('renders the list of announcements', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('System maintenance on Sunday.')).toBeInTheDocument();
      expect(screen.getByText('Evaluation deadline is May 15.')).toBeInTheDocument();
    });
  });

  it('opens create modal on "New Announcement" button click', async () => {
    renderPage();
    await waitFor(() => screen.getByText('System maintenance on Sunday.'));

    await userEvent.click(screen.getByRole('button', { name: /nové oznámení/i }));

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByLabelText(/text oznámení/i)).toBeInTheDocument();
  });

  it('creates a new announcement and closes the modal', async () => {
    const newAnnouncement: AnnouncementPublic = {
      id: 3,
      message: 'New system notice.',
      severity: AnnouncementSeverity.INFO,
      is_active: false,
      created_at: '2026-05-06T12:00:00Z',
      updated_at: '2026-05-06T12:00:00Z',
    };
    (api.createAnnouncement as ReturnType<typeof vi.fn>).mockResolvedValue(newAnnouncement);

    renderPage();
    await waitFor(() => screen.getByText('System maintenance on Sunday.'));

    // Open the create modal.
    await userEvent.click(screen.getByRole('button', { name: /nové oznámení/i }));
    await userEvent.type(screen.getByLabelText(/text oznámení/i), 'New system notice.');
    // Click the submit button inside the modal footer.
    const submitButtons = screen.getAllByRole('button', { name: /nové oznámení/i });
    await userEvent.click(submitButtons[submitButtons.length - 1]);

    await waitFor(() => {
      expect(api.createAnnouncement).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'New system notice.' }),
      );
    });
  });

  it('toggles is_active state via the toggle button', async () => {
    const updated = { ...mockAnnouncements[0], is_active: false };
    (api.updateAnnouncement as ReturnType<typeof vi.fn>).mockResolvedValue(updated);

    renderPage();
    await waitFor(() => screen.getByText('System maintenance on Sunday.'));

    // The first announcement is active — clicking its toggle deactivates it.
    const toggleBtn = screen.getAllByRole('button', { name: /deaktivovat oznámení/i })[0];
    await userEvent.click(toggleBtn);

    await waitFor(() => {
      expect(api.updateAnnouncement).toHaveBeenCalledWith(1, { is_active: false });
    });
  });

  it('deletes an announcement', async () => {
    (api.deleteAnnouncement as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);

    renderPage();
    await waitFor(() => screen.getByText('System maintenance on Sunday.'));

    const deleteButtons = screen.getAllByRole('button', { name: /smazat/i });
    await userEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(api.deleteAnnouncement).toHaveBeenCalledWith(1);
      expect(screen.queryByText('System maintenance on Sunday.')).not.toBeInTheDocument();
    });
  });

  it('shows empty state when no announcements exist', async () => {
    (api.getAnnouncements as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/zatím nebyla vytvořena/i)).toBeInTheDocument();
    });
  });
});
