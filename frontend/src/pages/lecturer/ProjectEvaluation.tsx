import { useLanguage } from '@/contexts/LanguageContext';

export const ProjectEvaluation = () => {
  const { t } = useLanguage();

  return <h1>{t('lecturer.projectEvaluation.title')}</h1>;
};
