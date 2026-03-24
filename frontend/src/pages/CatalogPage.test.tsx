import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import CatalogPage from './CatalogPage';
import { LanguageProvider } from '../contexts/LanguageContext';

const renderCatalogPage = () =>
  render(
    <MemoryRouter>
      <LanguageProvider>
        <CatalogPage />
      </LanguageProvider>
    </MemoryRouter>,
  );

describe('CatalogPage', () => {
  it('renders page heading', () => {
    renderCatalogPage();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Prohlížeč projektů');
  });

  it('renders search input', () => {
    renderCatalogPage();
    expect(screen.getByPlaceholderText(/hledat projekt/i)).toBeInTheDocument();
  });

  it('renders subject and year filter selects', () => {
    renderCatalogPage();
    expect(screen.getByText(/všechny předměty/i)).toBeInTheDocument();
    expect(screen.getByText(/všechny roky/i)).toBeInTheDocument();
  });
});
