import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { render, screen, waitFor, act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
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
    min_score: 50,
    lecturers: []
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
    const router = createMemoryRouter(
      [
        {
          path: "/student/project/:id/evaluate",
          element: <CourseEvaluation />,
        },
        {
          path: "/student",
          element: <div>Student Zone</div>,
        }
      ],
      {
        initialEntries: ['/student/project/101/evaluate'],
      }
    );

    let result;
    await act(async () => {
      result = render(
        <LanguageProvider>
          <AuthProvider>
            <RouterProvider router={router} />
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
      expect(screen.getByRole('heading', { level: 1, name: /Hodnocen\u00ed p\u0159edm\u011btu/i })).toBeInTheDocument();
    });
  });

  it('allows filling the form and saving', async () => {
    const user = userEvent.setup();
    (api.submitCourseEvaluation as Mock).mockResolvedValue({ message: 'Success' });
    
    // Mock confirm
    window.confirm = vi.fn().mockReturnValue(true);
    
    await renderEval();
    
    await waitFor(() => {
      expect(screen.getByText('Project Alpha')).toBeInTheDocument();
      // Strengths/Improvements labels/placeholders
      expect(screen.queryAllByPlaceholderText(/Co se vám na předmětu líbilo/i)).toHaveLength(1);
    });
    // Set rating
    await user.click(screen.getByRole('button', { name: /Hodnotit 3 hvězdičkami/i }));
    // Fill course eval
    const strengthsInput = screen.getByLabelText(/Silné stránky předmětu/i);
    await user.type(strengthsInput, 'Great course');

    const improvementsInput = screen.getByLabelText(/Prostor ke zlepšení předmětu/i);
    await user.type(improvementsInput, 'More labs');

    // Fill peer eval
    const peerStrengths = screen.getByPlaceholderText(/Popište silné stránky, přínos pro tým/i);
    await user.type(peerStrengths, 'Good mate');

    const peerImprovements = screen.getByPlaceholderText(/Kde vidíte rezervy, co by mohl dělat jinak/i);
    await user.type(peerImprovements, 'None');
    
    // Click save
    const saveButton = screen.getByRole('button', { name: /Uložit změny/i });
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(api.submitCourseEvaluation).toHaveBeenCalledWith(
        expect.any(Number),
        expect.objectContaining({ submitted: true })
      );
    });
  });

  it('validates remaining points before submission', async () => {
    await renderEval();
    
    await waitFor(() => {
      expect(screen.getByText('Project Alpha')).toBeInTheDocument();
      expect(screen.queryAllByLabelText(/Points for/i)).toHaveLength(1);
    });

    const slider = screen.getByLabelText(/Points for Teammate One/i);
    fireEvent.change(slider, { target: { value: '15' } });

    await waitFor(() => {
      expect(screen.queryAllByText(/Zbývající body: -5/i).length).toBeGreaterThan(0);
      expect(screen.getByRole('button', { name: /Uložit změny/i })).toBeDisabled();
    });
  });

  it('loads existing data', async () => {
    (api.getCourseEvaluation as Mock).mockResolvedValue({
      teammates: mockProject.members.filter(m => m.id !== mockUser.id),
      peer_bonus_budget: 10,
      current_evaluation: {
        id: 1,
        student_id: 1,
        rating: 4,
        strengths: 'Previous strengths',
        improvements: 'Previous improvements',
        submitted: true,
        updated_at: '2026-01-01T00:00:00Z'
      },
      authored_peer_feedback: [
        {
          course_evaluation_id: 1,
          receiving_student_id: 2,
          strengths: 'Mate strengths',
          improvements: 'Mate improvements',
          bonus_points: 12
        }
      ],
      results_unlocked: false
    });

    await renderEval();
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('Previous strengths')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Mate strengths')).toBeInTheDocument();
      expect(screen.getByText('12')).toBeInTheDocument();
    });
  });

  it('disables form when results are unlocked', async () => {
    (api.getProject as Mock).mockResolvedValue({
      ...mockProject,
      results_unlocked: true
    });

    await renderEval();
    
    await waitFor(() => {
      expect(screen.getByLabelText(/Silné stránky předmětu/i)).toBeDisabled();
      expect(screen.queryByRole('button', { name: /Uložit změny/i })).not.toBeInTheDocument();
    });
  });
});
