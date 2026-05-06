import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AnnouncementBanner } from './AnnouncementBanner';
import { AnnouncementPublic, AnnouncementSeverity } from '@/types';
import * as api from '@/api';

vi.mock('@/api', () => ({
  getActiveAnnouncement: vi.fn(),
}));

const mockAnnouncement: AnnouncementPublic = {
  id: 42,
  message: 'Planned maintenance on Sunday at 2 AM.',
  severity: AnnouncementSeverity.WARNING,
  is_active: true,
  created_at: '2026-05-01T10:00:00Z',
  updated_at: '2026-05-01T10:00:00Z',
};

describe('AnnouncementBanner', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders the active announcement message', async () => {
    (api.getActiveAnnouncement as ReturnType<typeof vi.fn>).mockResolvedValue(mockAnnouncement);

    render(<AnnouncementBanner />);

    await waitFor(() => {
      expect(screen.getByText('Planned maintenance on Sunday at 2 AM.')).toBeInTheDocument();
    });
  });

  it('renders nothing when no active announcement exists', async () => {
    (api.getActiveAnnouncement as ReturnType<typeof vi.fn>).mockResolvedValue(null);

    const { container } = render(<AnnouncementBanner />);

    await waitFor(() => {
      expect(container).toBeEmptyDOMElement();
    });
  });

  it('hides the banner after clicking dismiss', async () => {
    (api.getActiveAnnouncement as ReturnType<typeof vi.fn>).mockResolvedValue(mockAnnouncement);

    render(<AnnouncementBanner />);
    await waitFor(() => screen.getByText('Planned maintenance on Sunday at 2 AM.'));

    await userEvent.click(screen.getByRole('button', { name: /dismiss/i }));

    expect(screen.queryByText('Planned maintenance on Sunday at 2 AM.')).not.toBeInTheDocument();
  });

  it('persists dismissal in localStorage keyed by announcement ID', async () => {
    (api.getActiveAnnouncement as ReturnType<typeof vi.fn>).mockResolvedValue(mockAnnouncement);

    render(<AnnouncementBanner />);
    await waitFor(() => screen.getByText('Planned maintenance on Sunday at 2 AM.'));

    await userEvent.click(screen.getByRole('button', { name: /dismiss/i }));

    expect(localStorage.getItem('announcement-dismissed-42')).toBe('true');
  });

  it('does not show a previously dismissed announcement', async () => {
    // Pre-set the dismissed flag before rendering.
    localStorage.setItem('announcement-dismissed-42', 'true');
    (api.getActiveAnnouncement as ReturnType<typeof vi.fn>).mockResolvedValue(mockAnnouncement);

    const { container } = render(<AnnouncementBanner />);

    // Wait for the async fetch to settle, then assert nothing is shown.
    await waitFor(() => {
      expect(container).toBeEmptyDOMElement();
    });
  });

  it('has an accessible alert role', async () => {
    (api.getActiveAnnouncement as ReturnType<typeof vi.fn>).mockResolvedValue(mockAnnouncement);

    render(<AnnouncementBanner />);
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
