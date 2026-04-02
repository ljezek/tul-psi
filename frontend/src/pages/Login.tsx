import { useLanguage } from '@/contexts/LanguageContext';

export const Login = () => {
  const { t } = useLanguage();
  return <h1>{t('nav.login')}</h1>;
};
