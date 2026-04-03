import { useLanguage } from '@/contexts/LanguageContext';

export const CourseProjects = () => {
  const { t } = useLanguage();

  return <h1>{t('lecturer.courseProjects.heading')}</h1>;
};
