import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { LanguageProvider, useLanguage } from './LanguageContext';

// Test component that uses the language context
const TestComponent = () => {
  const { language, setLanguage, t } = useLanguage();

  return (
    <div>
      <p data-testid="current-language">{language}</p>
      <p data-testid="translated-title">{t('app.title')}</p>
      <p data-testid="translated-fallback">{t('non.existent.key')}</p>
      <button onClick={() => setLanguage(language === 'cs' ? 'en' : 'cs')}>
        Toggle Language
      </button>
    </div>
  );
};

describe('LanguageContext', () => {
  describe('Translation function (t)', () => {
    it('should return Czech translation by default', () => {
      render(
        <LanguageProvider>
          <TestComponent />
        </LanguageProvider>
      );

      expect(screen.getByTestId('current-language')).toHaveTextContent('cs');
      expect(screen.getByTestId('translated-title')).toHaveTextContent(
        'Katalog Projektů'
      );
    });

    it('should return English translation when language is set to en', async () => {
      const user = userEvent.setup();
      render(
        <LanguageProvider>
          <TestComponent />
        </LanguageProvider>
      );

      const toggleButton = screen.getByRole('button', { name: /toggle language/i });
      await user.click(toggleButton);

      expect(screen.getByTestId('current-language')).toHaveTextContent('en');
      expect(screen.getByTestId('translated-title')).toHaveTextContent(
        'Project Catalog'
      );
    });

    it('should fall back to key name if translation is not found', () => {
      render(
        <LanguageProvider>
          <TestComponent />
        </LanguageProvider>
      );

      expect(screen.getByTestId('translated-fallback')).toHaveTextContent(
        'non.existent.key'
      );
    });
  });

  describe('useLanguage hook', () => {
    it('should throw error when used outside LanguageProvider', () => {
      const InvalidComponent = () => {
        useLanguage();
        return <div>Test</div>;
      };

      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<InvalidComponent />);
      }).toThrow('useLanguage must be used within a LanguageProvider');

      consoleSpy.mockRestore();
    });

    it('should provide language switching functionality', async () => {
      const user = userEvent.setup();
      render(
        <LanguageProvider>
          <TestComponent />
        </LanguageProvider>
      );

      // Start in Czech
      expect(screen.getByTestId('current-language')).toHaveTextContent('cs');

      // Toggle to English
      await user.click(screen.getByRole('button'));
      expect(screen.getByTestId('current-language')).toHaveTextContent('en');

      // Toggle back to Czech
      await user.click(screen.getByRole('button'));
      expect(screen.getByTestId('current-language')).toHaveTextContent('cs');
    });
  });
});
