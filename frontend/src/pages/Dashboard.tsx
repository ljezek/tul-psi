import { useLanguage } from '@/contexts/LanguageContext';

export const Dashboard = () => {
  const { t } = useLanguage();
  return <h1>{t('dashboard.title')}</h1>;
};
