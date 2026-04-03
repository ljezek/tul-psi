import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Dashboard } from './Dashboard';
import { LanguageProvider } from '@/contexts/LanguageContext';
import * as api from '@/api';
import { ProjectPublic, CourseListItem, CourseTerm, ProjectType } from '@/types';

// Mock the API module
vi.mock('@/api', () => ({
  getProjects: vi.fn(),
  getCourses: vi.fn(),
}));

const mockProjects: ProjectPublic[] = [
  {
    id: 1,
    title: 'React App',
    description: 'A cool React application',
    technologies: ['React', 'TypeScript'],
    academic_year: 2023,
    github_url: 'https://github.com/test/react',
    live_url: null,
    course: {
      code: 'PR1',
      name: 'Programming 1',
      syllabus: null,
      term: CourseTerm.WINTER,
      project_type: ProjectType.INDIVIDUAL,
      min_score: 50,
      peer_bonus_budget: null,
      evaluation_criteria: [],
      links: [],
      lecturers: []
    },
    members: [{ id: 1, name: 'John Doe', github_alias: 'jdoe', email: 'john@tul.cz' }],
    results_unlocked: false,
    project_evaluations: [],
    course_evaluations: [],
    received_peer_feedback: [],
    authored_peer_feedback: []
  },
  {
    id: 2,
    title: 'Python Tool',
    description: 'Data processing with Python',
    technologies: ['Python', 'Pandas'],
    academic_year: 2022,
    github_url: null,
    live_url: 'https://demo.com',
    course: {
      code: 'DS1',
      name: 'Data Science 1',
      syllabus: null,
      term: CourseTerm.SUMMER,
      project_type: ProjectType.TEAM,
      min_score: 60,
      peer_bonus_budget: 10,
      evaluation_criteria: [],
      links: [],
      lecturers: []
    },
    members: [{ id: 2, name: 'Jane Smith', github_alias: 'jsmith', email: 'jane@tul.cz' }],
    results_unlocked: true,
    project_evaluations: [],
    course_evaluations: [],
    received_peer_feedback: [],
    authored_peer_feedback: []
  }
];

const mockCourses: CourseListItem[] = [
  {
    id: 1,
    code: 'PR1',
    name: 'Programming 1',
    syllabus: null,
    lecturer_names: ['Dr. Test'],
    stats: { project_count: 1, academic_years: [2023] }
  },
  {
    id: 2,
    code: 'DS1',
    name: 'Data Science 1',
    syllabus: null,
    lecturer_names: ['Prof. Data'],
    stats: { project_count: 1, academic_years: [2022] }
  }
];

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getProjects as Mock).mockResolvedValue(mockProjects);
    (api.getCourses as Mock).mockResolvedValue(mockCourses);
  });

  const renderDashboard = () => {
    return render(
      <LanguageProvider>
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      </LanguageProvider>
    );
  };

  it('renders all projects initially', async () => {
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText('React App')).toBeInTheDocument();
      expect(screen.getByText('Python Tool')).toBeInTheDocument();
    });
  });

  it('filters projects by search text', async () => {
    const user = userEvent.setup();
    renderDashboard();
    
    await waitFor(() => screen.getByText('React App'));
    
    const searchInput = screen.getByPlaceholderText(/Hledat projekt nebo technologii/i);
    await user.type(searchInput, 'Python');
    
    expect(screen.queryByText('React App')).not.toBeInTheDocument();
    expect(screen.getByText('Python Tool')).toBeInTheDocument();
  });

  it('filters projects by course', async () => {
    const user = userEvent.setup();
    renderDashboard();
    
    await waitFor(() => screen.getByText('React App'));
    
    const courseSelect = screen.getByLabelText(/Předmět/i);
    await user.selectOptions(courseSelect, 'DS1');
    
    expect(screen.queryByText('React App')).not.toBeInTheDocument();
    expect(screen.getByText('Python Tool')).toBeInTheDocument();
  });

  it('filters projects by academic year', async () => {
    const user = userEvent.setup();
    renderDashboard();
    
    await waitFor(() => screen.getByText('React App'));
    
    const yearSelect = screen.getByLabelText(/Akademický rok/i);
    await user.selectOptions(yearSelect, '2022');
    
    expect(screen.queryByText('React App')).not.toBeInTheDocument();
    expect(screen.getByText('Python Tool')).toBeInTheDocument();
  });

  it('shows no results state and clears filters', async () => {
    const user = userEvent.setup();
    renderDashboard();
    
    await waitFor(() => screen.getByText('React App'));
    
    const searchInput = screen.getByPlaceholderText(/Hledat projekt nebo technologii/i);
    await user.type(searchInput, 'Nonexistent');
    
    expect(screen.getByText(/Nebyly nalezeny žádné projekty/i)).toBeInTheDocument();
    
    const clearButton = screen.getByRole('button', { name: /Zrušit filtry/i });
    await user.click(clearButton);
    
    expect(screen.getByText('React App')).toBeInTheDocument();
    expect(screen.getByText('Python Tool')).toBeInTheDocument();
  });
});
