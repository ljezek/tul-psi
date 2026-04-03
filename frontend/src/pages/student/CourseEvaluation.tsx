import { useLanguage } from "@/contexts/LanguageContext";

export const CourseEvaluation = () => {
  const { t } = useLanguage();

  return <h1>{t("student.courseEvaluation.title")}</h1>;
};
