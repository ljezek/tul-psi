import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { render, screen, waitFor, act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { CourseEvaluation } from './CourseEvaluation';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { AuthProvider } from '@/contexts/AuthContext';
import * as api from '@/api';
import { UserRole, ProjectType } from '@/types';

// Mock API
vi.mock('@/api', async (importOriginal) => {
  const actual = await importOriginal<typeof api>();
  return {
    ...actual,
    getProject: vi.fn(),
    getCourseEvaluation: vi.fn(),
    submitCourseEvaluation: vi.fn(),
    getCurrentUser: vi.fn(),
  };
});

const mockUser = {
  id: 1,
  email: 'student@tul.cz',
  name: 'Test Student',
  role: UserRole.STUDENT,
  is_active: true,
};

const mockProject = {
  id: 101,
  title: 'Project Alpha',
  course: { 
    id: 1, 
    code: 'C1', 
    name: 'Course 1', 
    project_type: ProjectType.TEAM,
    peer_bonus_budget: 10,
    evaluation_criteria: [],
    min_score: 50
  },
  members: [
    { id: 1, name: 'Test Student', email: 's@tul.cz' },
    { id: 2, name: 'Teammate One', email: 't1@tul.cz' }
  ],
  results_unlocked: false,
  course_evaluations: [],
  received_peer_feedback: [],
  project_evaluations: []
};

describe('CourseEvaluation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getCurrentUser as Mock).mockResolvedValue(mockUser);
    (api.getProject as Mock).mockResolvedValue(mockProject);
    (api.getCourseEvaluation as Mock).mockRejectedValue({ status: 404 });
  });

  const renderEval = async () => {
    let result;
    await act(async () => {
      result = render(
        <LanguageProvider>
          <AuthProvider>
            <MemoryRouter initialEntries={['/student/project/101/evaluate']}>
              <Routes>
                <Route path="/student/project/:id/evaluate" element={<CourseEvaluation />} />
              </Routes>
            </MemoryRouter>
          </AuthProvider>
        </LanguageProvider>
      );
    });
    return result;
  };

  it('renders evaluation form and teammate info', async () => {
    await renderEval();
    
    await waitFor(() => {
      expect(screen.getByText('Project Alpha')).toBeInTheDocument();
      expect(screen.getByText('Teammate One')).toBeInTheDocument();
      // Use role+level to disambiguate from the section heading and star-rating
      // label that share the same translated text.
      expect(screen.getByRole('heading', { level: 1, name: /Hodnocen\u00ed p\u0159edm\u011btu/i })).toBeInTheDocument();
    });
  });

  it('allows filling the form and submitting', async () => {
    const user = userEvent.setup();
    (api.submitCourseEvaluation as Mock).mockResolvedValue({ message: 'Success' });
    
    // Mock confirm
    window.confirm = vi.fn().mockReturnValue(true);
    
    await renderEval();
    
    // Wait until auth resolves and only Teammate One (not the current user) shows as peer.
    // Both the subject-eval and peer-eval sections share the same placeholder text, so we
    // wait for a stable state (2 elements for strengths_ph: one per section).
    await waitFor(() => {
      expect(screen.getByText('Project Alpha')).toBeInTheDocument();
      expect(screen.queryAllByPlaceholderText(/Popište silné stránky/i)).toHaveLength(2);
    });
    // Set rating (required — submit button stays disabled while rating === 0).
    await user.click(screen.getByRole('button', { name: 'Rate 3' }));
    // Fill subject eval (these textareas have accessible labels via htmlFor).
    const strengthsInput = screen.getByLabelText(/Silné stránky předmětu/i);
    await user.type(strengthsInput, 'Great course');

    const improvementsInput = screen.getByLabelText(/Prostor ke zlepšení předmětu/i);
    await user.type(improvementsInput, 'More labs');

    // Fill peer eval — the subject-eval section comes first in the DOM, so the
    // peer-eval textareas are always at index [1] of each placeholder group.
    const peerStrengths = screen.getAllByPlaceholderText(/Popište silné stránky, přínos pro tým/i)[1];
    await user.type(peerStrengths, 'Good mate');

    const peerImprovements = screen.getAllByPlaceholderText(/Kde vidíte rezervy, co by mohl dělat jinak/i)[1];
    await user.type(peerImprovements, 'None');
    
    // Click submit
    const submitButton = screen.getByRole('button', { name: /Odeslat hodnocení/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(api.submitCourseEvaluation).toHaveBeenCalled();
    });
  });

  it('validates remaining points before submission', async () => {
    await renderEval();
    
    // Wait until auth resolves so the teammate list is stable and initialPoints
    // won't be reset mid-test. Exactly one slider should be visible at that point.
    await waitFor(() => {
      expect(screen.getByText('Project Alpha')).toBeInTheDocument();
      expect(screen.queryAllByLabelText(/Points for/i)).toHaveLength(1);
    });

    // Change a slider to create imbalance. Range inputs are not text-editable so
    // we use fireEvent.change directly instead of userEvent.
    const slider = screen.getByLabelText(/Points for Teammate One/i);
    fireEvent.change(slider, { target: { value: '15' } });

    // Budget is 10 per person, there is only one teammate so totalBudget = 10.
    // With no other recipients to redistribute to, the hook keeps the new value
    // as-is, leaving remainingPoints = 10 - 15 = -5.
    
    await waitFor(() => {
      // Both the aria-live budget summary and the footer error banner contain
      // the remaining-points text, so use queryAllByText to avoid "multiple elements" errors.
      expect(screen.queryAllByText(/Zbývající body: -5/i).length).toBeGreaterThan(0);
      expect(screen.getByRole('button', { name: /Odeslat hodnocení/i })).toBeDisabled();
    });
  });
});
