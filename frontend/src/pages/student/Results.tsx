import { useLanguage } from '@/contexts/LanguageContext';

export const Results = () => {
  const { t } = useLanguage();

  return <h1>{t('student.results.title')}</h1>;
};
