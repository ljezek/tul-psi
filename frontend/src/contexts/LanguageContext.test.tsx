import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { LanguageProvider, useLanguage } from './LanguageContext';

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
        </LanguageProvider>,
      );

      expect(screen.getByTestId('current-language')).toHaveTextContent('cs');
      expect(screen.getByTestId('translated-title')).toHaveTextContent('Katalog Projektů');
    });

    it('should return English translation when language is set to en', async () => {
      const user = userEvent.setup();
      render(
        <LanguageProvider>
          <TestComponent />
        </LanguageProvider>,
      );

      await user.click(screen.getByRole('button', { name: /toggle language/i }));

      expect(screen.getByTestId('current-language')).toHaveTextContent('en');
      expect(screen.getByTestId('translated-title')).toHaveTextContent('Project Catalog');
    });

    it('should fall back to key name if translation is not found', () => {
      render(
        <LanguageProvider>
          <TestComponent />
        </LanguageProvider>,
      );

      expect(screen.getByTestId('translated-fallback')).toHaveTextContent('non.existent.key');
    });
  });

  describe('useLanguage hook', () => {
    it('should throw error when used outside LanguageProvider', () => {
      const InvalidComponent = () => {
        useLanguage();
        return <div>Test</div>;
      };

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<InvalidComponent />);
      }).toThrow('useLanguage must be used within a LanguageProvider');

      consoleSpy.mockRestore();
    });

    it('should support toggling language back and forth', async () => {
      const user = userEvent.setup();
      render(
        <LanguageProvider>
          <TestComponent />
        </LanguageProvider>,
      );

      expect(screen.getByTestId('current-language')).toHaveTextContent('cs');

      await user.click(screen.getByRole('button'));
      expect(screen.getByTestId('current-language')).toHaveTextContent('en');

      await user.click(screen.getByRole('button'));
      expect(screen.getByTestId('current-language')).toHaveTextContent('cs');
    });
  });
});
