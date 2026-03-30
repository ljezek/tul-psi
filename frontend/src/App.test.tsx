import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import App from './App';

describe('App', () => {
  it('renders the landing page heading', () => {
    render(<App />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Katalog Projektů');
  });

  it('renders the university subtitle', () => {
    render(<App />);
    expect(screen.getByText(/Technická univerzita v Liberci/i)).toBeInTheDocument();
  });
});
