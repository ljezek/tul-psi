import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import Navbar from './Navbar';
import { LanguageProvider } from '../contexts/LanguageContext';

const renderNavbar = () =>
  render(
    <MemoryRouter>
      <LanguageProvider>
        <Navbar />
      </LanguageProvider>
    </MemoryRouter>,
  );

describe('Navbar', () => {
  it('renders the logo text', () => {
    renderNavbar();
    expect(screen.getByText('FM')).toBeInTheDocument();
  });

  it('renders navigation links', () => {
    renderNavbar();
    expect(screen.getByRole('link', { name: /projekty/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /studentská zóna/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /administrace/i })).toBeInTheDocument();
  });

  it('toggles language between CS and EN', async () => {
    const user = userEvent.setup();
    renderNavbar();

    const langButton = screen.getAllByLabelText(/toggle language/i)[0];
    expect(langButton).toHaveTextContent('CS');

    await user.click(langButton);
    expect(langButton).toHaveTextContent('EN');
  });

  it('shows mobile menu toggle button on small screens', () => {
    renderNavbar();
    expect(screen.getByLabelText('Toggle menu')).toBeInTheDocument();
  });
});
