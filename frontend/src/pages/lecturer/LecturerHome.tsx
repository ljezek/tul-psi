import { useLanguage } from '@/contexts/LanguageContext';

export const LecturerHome = () => {
  const { t } = useLanguage();
  return <h1>{t('nav.lecturer_panel')}</h1>;
};
