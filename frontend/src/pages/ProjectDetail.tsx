import { useLanguage } from '@/context/LanguageContext';

export const ProjectDetail = () => {
  const { t } = useLanguage();

  return <h1>{t('projectDetail.title')}</h1>;
};
