import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import LandingPage from './LandingPage';
import { LanguageProvider } from '../contexts/LanguageContext';

const renderLandingPage = () =>
  render(
    <MemoryRouter>
      <LanguageProvider>
        <LandingPage />
      </LanguageProvider>
    </MemoryRouter>,
  );

describe('LandingPage', () => {
  it('renders hero title', () => {
    renderLandingPage();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Katalog projektů FM TUL');
  });

  it('renders CTA links to catalog and student zone', () => {
    renderLandingPage();
    const browseLink = screen.getByRole('link', { name: /prohlédnout projekty/i });
    const studentLink = screen.getByRole('link', { name: /studentská zóna/i });

    expect(browseLink).toHaveAttribute('href', '/catalog');
    expect(studentLink).toHaveAttribute('href', '/student');
  });

  it('renders three feature cards', () => {
    renderLandingPage();
    expect(screen.getByRole('heading', { level: 3, name: /prohlížení projektů/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: /peer feedback/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: /správa kurzů/i })).toBeInTheDocument();
  });
});
