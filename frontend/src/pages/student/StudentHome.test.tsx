import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { StudentHome } from './StudentHome';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { AuthProvider } from '@/contexts/AuthContext';
import * as api from '@/api';
import { UserRole, ProjectType } from '@/types';

// Mock API
vi.mock('@/api', async (importOriginal) => {
  const actual = await importOriginal<typeof api>();
  return {
    ...actual,
    getProjects: vi.fn(),
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

const mockProjects = [
  {
    id: 101,
    title: 'Project Alpha',
    academic_year: 2024,
    course: { id: 1, code: 'C1', name: 'Course 1', project_type: ProjectType.TEAM, lecturers: [{ name: 'L1' }], evaluation_criteria: [{ code: 'C1', description: 'Crit', max_score: 100 }], min_score: 50 },
    members: [{ id: 1, name: 'Test Student' }, { id: 2, name: 'Other' }],
    results_unlocked: true,
    course_evaluations: [{ student_id: 1, submitted: true }],
    project_evaluations: [{
      lecturer_id: 1,
      submitted: true,
      updated_at: '2024-01-01T00:00:00Z',
      scores: [{ criterion_code: 'C1', score: 80, strengths: '', improvements: '' }]
    }],
    submitted_lecturer_count: 1,
    submitted_student_count: 2
  },
  {
    id: 102,
    title: 'Project Beta',
    academic_year: 2024,
    course: { id: 2, code: 'C2', name: 'Course 2', project_type: ProjectType.INDIVIDUAL, lecturers: [{ name: 'L1' }], evaluation_criteria: [{ code: 'C2', description: 'Crit', max_score: 100 }], min_score: 50 },
    members: [{ id: 1, name: 'Test Student' }],
    results_unlocked: false,
    course_evaluations: [{ student_id: 1, submitted: false }],
    project_evaluations: [],
    submitted_lecturer_count: 0,
    submitted_student_count: 0
  },
  {
    id: 103,
    title: 'Other Project',
    academic_year: 2024,
    course: { id: 3, code: 'C3', name: 'Course 3', project_type: ProjectType.TEAM, lecturers: [{ name: 'L1' }], evaluation_criteria: [] },
    members: [{ id: 3, name: 'Someone Else' }],
    results_unlocked: false,
    course_evaluations: [],
    project_evaluations: [],
    submitted_lecturer_count: 0,
    submitted_student_count: 0
  }
];

describe('StudentHome', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getCurrentUser as Mock).mockResolvedValue(mockUser);
    (api.getProjects as Mock).mockResolvedValue(mockProjects);
  });

  const renderHome = async () => {
    let result;
    await act(async () => {
      result = render(
        <LanguageProvider>
          <AuthProvider>
            <MemoryRouter>
              <StudentHome />
            </MemoryRouter>
          </AuthProvider>
        </LanguageProvider>
      );
    });
    return result;
  };

  it('renders only projects where user is a member', async () => {
    await renderHome();
    
    await waitFor(() => {
      expect(screen.getByText('Project Alpha')).toBeInTheDocument();
      expect(screen.getByText('Project Beta')).toBeInTheDocument();
      expect(screen.queryByText('Other Project')).not.toBeInTheDocument();
    });
  });

  it('shows correct status badges for evaluations', async () => {
    await renderHome();
    
    await waitFor(() => {
      // Project Alpha: Submitted
      const alphaCard = screen.getByText('Project Alpha').closest('div.group');
      expect(alphaCard).toHaveTextContent(/Odesláno/i);
      
      // Project Beta: Draft (Koncept)
      const betaCard = screen.getByText('Project Beta').closest('div.group');
      expect(betaCard).toHaveTextContent(/Koncept/i);
    });
  });

  it('shows correct status badges for results', async () => {
    await renderHome();
    
    await waitFor(() => {
      // Project Alpha: Passed
      const alphaCard = screen.getByText('Project Alpha').closest('div.group');
      expect(alphaCard).toHaveTextContent(/SPLNĚNO/i);
      
      // Project Beta: Pending
      const betaCard = screen.getByText('Project Beta').closest('div.group');
      expect(betaCard).toHaveTextContent(/student\.locked/i);
    });
  });

  it('shows empty state when no projects assigned', async () => {
    (api.getProjects as Mock).mockResolvedValue([]);
    await renderHome();
    
    await waitFor(() => {
      expect(screen.getByText(/Nejste přiřazeni k žádnému projektu/i)).toBeInTheDocument();
    });
  });

  it('shows SHOW RESULTS button when results_unlocked', async () => {
    await renderHome();

    await waitFor(() => {
      expect(screen.getByText(/ZOBRAZIT VÝSLEDKY/i)).toBeInTheDocument();
    });
  });
});
