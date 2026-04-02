import { useLanguage } from '@/contexts/LanguageContext';

export const StudentHome = () => {
  const { t } = useLanguage();
  return <h1>{t('student.zone_title')}</h1>;
};
