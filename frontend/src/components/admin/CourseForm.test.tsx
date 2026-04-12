import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CourseForm, CourseFormProps } from './CourseForm';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { ProjectType } from '@/types';

import { Mock } from 'vitest';

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

const renderCourseForm = (props: Partial<CourseFormProps> = {}) => {
  const defaultProps: CourseFormProps = {
    onSubmit: vi.fn().mockResolvedValue(undefined),
    isLoading: false,
    error: null,
  };

  return render(
    <LanguageProvider>
      <CourseForm
        {...defaultProps}
        {...props}
      />
    </LanguageProvider>
  );
};

describe('CourseForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as Mock).mockReturnValue({
      user: { email: 'test@tul.cz' },
    });
  });

  it('renders with new default values', () => {
    renderCourseForm();

    // Min score should be 40 (using Czech label as it is default)
    const minScoreInput = screen.getByLabelText(/Minimální skóre/i) as HTMLInputElement;
    expect(minScoreInput.value).toBe('40');

    // Project type should be INDIVIDUAL
    const projectTypeSelect = screen.getByLabelText(/Typ projektu/i) as HTMLSelectElement;
    expect(projectTypeSelect.value).toBe(ProjectType.INDIVIDUAL);

    // Should have 3 evaluation criteria
    expect(screen.getAllByText(/Kritérium/i).length).toBeGreaterThanOrEqual(3);
    expect(screen.getByDisplayValue(/Specifikace a dokumentace/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue(/Kvalita kódu/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue(/Testování a nasazení/i)).toBeInTheDocument();
  });

  it('sets peer bonus budget to 10 when switching to TEAM project type', async () => {
    renderCourseForm();

    const projectTypeSelect = screen.getByLabelText(/Typ projektu/i) as HTMLSelectElement;
    fireEvent.change(projectTypeSelect, { target: { value: ProjectType.TEAM } });

    // Peer bonus budget should appear and be 10
    const peerBonusInput = screen.getByLabelText(/Peer Bonus rozpočet/i) as HTMLInputElement;
    expect(peerBonusInput.value).toBe('10');
  });

  it('has updated peer bonus budget hint', () => {
    renderCourseForm();

    // Switch to TEAM to see the hint
    const projectTypeSelect = screen.getByLabelText(/Typ projektu/i) as HTMLSelectElement;
    fireEvent.change(projectTypeSelect, { target: { value: ProjectType.TEAM } });

    // Check for Czech hint content
    expect(screen.getByText(/Rozpočet bodů k rozdělení na jednoho spoluhráče/i)).toBeInTheDocument();
    expect(screen.getByText(/\[0, 2 \* rozpočet\]/i)).toBeInTheDocument();
  });
});
