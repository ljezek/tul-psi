import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Language } from '../types';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const translations: Record<string, Record<Language, string>> = {
  // Navigation & Roles
  'app.title': { cs: 'Katalog Projektů', en: 'Project Catalog' },
  'nav.catalog': { cs: 'Projekty', en: 'Projects' },
  'nav.student': { cs: 'Studentská zóna', en: 'Student Zone' },
  'nav.admin': { cs: 'Administrace', en: 'Admin' },
  'role.public': { cs: 'Veřejnost', en: 'Public' },
  'role.student': { cs: 'Student', en: 'Student' },
  'role.lecturer': { cs: 'Lektor', en: 'Lecturer' },
  'footer.copyright': {
    cs: 'Fakulta mechatroniky, informatiky a mezioborových studií TUL.',
    en: 'Faculty of Mechatronics, Informatics and Interdisciplinary Studies TUL.',
  },

  // Landing page
  'landing.hero_title': { cs: 'Katalog projektů FM TUL', en: 'FM TUL Project Catalog' },
  'landing.hero_subtitle': {
    cs: 'Centrální místo pro sdílení a hodnocení studentských projektů na Fakultě mechatroniky, informatiky a mezioborových studií.',
    en: 'A central hub for sharing and evaluating student projects at the Faculty of Mechatronics, Informatics and Interdisciplinary Studies.',
  },
  'landing.cta_browse': { cs: 'Prohlédnout projekty', en: 'Browse Projects' },
  'landing.cta_student': { cs: 'Studentská zóna', en: 'Student Zone' },
  'landing.features_title': { cs: 'Co nabízí katalog?', en: 'What does the catalog offer?' },
  'landing.feature_browse_title': { cs: 'Prohlížení projektů', en: 'Browse Projects' },
  'landing.feature_browse_desc': {
    cs: 'Filtrujte projekty podle předmětu, roku nebo technologie.',
    en: 'Filter projects by subject, year, or technology.',
  },
  'landing.feature_feedback_title': { cs: 'Peer feedback', en: 'Peer Feedback' },
  'landing.feature_feedback_desc': {
    cs: 'Studenti si vzájemně poskytují konstruktivní zpětnou vazbu.',
    en: 'Students provide each other with constructive feedback.',
  },
  'landing.feature_admin_title': { cs: 'Správa kurzů', en: 'Course Management' },
  'landing.feature_admin_desc': {
    cs: 'Lektoři spravují předměty, projekty a hodnocení.',
    en: 'Lecturers manage subjects, projects, and evaluations.',
  },

  // Dashboard / Catalog page
  'dashboard.title': { cs: 'Prohlížeč projektů', en: 'Project Browser' },
  'dashboard.subtitle': {
    cs: 'Prozkoumejte inovativní práce studentů FM TUL.',
    en: 'Explore innovative work by FM TUL students.',
  },
  'dashboard.search_placeholder': {
    cs: 'Hledat projekt nebo technologii...',
    en: 'Search project or technology...',
  },
  'dashboard.filter_subject': { cs: 'Předmět', en: 'Subject' },
  'dashboard.filter_year': { cs: 'Akademický rok', en: 'Academic Year' },
  'dashboard.all_subjects': { cs: 'Všechny předměty', en: 'All Subjects' },
  'dashboard.all_years': { cs: 'Všechny roky', en: 'All Years' },
  'dashboard.no_results': { cs: 'Nebyly nalezeny žádné projekty', en: 'No projects found' },
  'dashboard.coming_soon': {
    cs: 'Seznam projektů bude dostupný po propojení s backendem.',
    en: 'Project list will be available once connected to the backend.',
  },

  // Student zone
  'student.zone_title': { cs: 'Studentská zóna', en: 'Student Zone' },
  'student.zone_desc': {
    cs: 'Přihlaste se svým TUL účtem pro přístup k hodnocení projektů a peer feedbacku.',
    en: 'Sign in with your TUL account to access project evaluations and peer feedback.',
  },
  'student.coming_soon': {
    cs: 'Přihlášení bude dostupné po propojení s backendem.',
    en: 'Sign-in will be available once connected to the backend.',
  },

  // Admin panel
  'admin.title': { cs: 'Administrace lektora', en: 'Lecturer Administration' },
  'admin.desc': {
    cs: 'Přihlaste se jako lektor pro správu předmětů, projektů a hodnocení.',
    en: 'Sign in as a lecturer to manage subjects, projects, and feedback.',
  },
  'admin.coming_soon': {
    cs: 'Administrace bude dostupná po propojení s backendem.',
    en: 'Administration will be available once connected to the backend.',
  },
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<Language>('cs');

  const t = (key: string): string => {
    return translations[key]?.[language] ?? key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
