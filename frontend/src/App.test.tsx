import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import App from './App';

describe('App', () => {
  it('renders the landing page at root route', () => {
    render(<App />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Katalog projektů FM TUL',
    );
  });

  it('renders the navbar with logo', () => {
    render(<App />);
    expect(screen.getByText('FM')).toBeInTheDocument();
  });

  it('renders the footer', () => {
    render(<App />);
    expect(
      screen.getByText(/Technická univerzita v Liberci/i),
    ).toBeInTheDocument();
  });
});
