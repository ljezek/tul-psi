import { createContext, useContext, useState, ReactNode } from 'react';

type Language = 'cs' | 'en';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const translations: Record<string, Record<Language, string>> = {
  // Navigation & Roles
  'app.title': { cs: 'Katalog Projektů', en: 'Project Catalog' },
  'nav.dashboard': { cs: 'Projekty', en: 'Projects' },
  'nav.courses': { cs: 'Předměty', en: 'Courses' },
  'nav.student_zone': { cs: 'Studentská zóna', en: 'Student Zone' },
  'nav.lecturer_panel': { cs: 'Panel Lektora', en: 'Lecturer Panel' },
  'nav.login': { cs: 'Přihlásit', en: 'Log In' },
  'nav.logout': { cs: 'Odhlásit', en: 'Log Out' },
  'nav.open_menu': { cs: 'Otevřít menu', en: 'Open menu' },
  'nav.close_menu': { cs: 'Zavřít menu', en: 'Close menu' },
  'role.public': { cs: 'Veřejnost', en: 'Public' },
  'role.student': { cs: 'Student', en: 'Student' },
  'role.lecturer': { cs: 'Lektor', en: 'Lecturer' },
  'role.select_demo': { cs: 'Vyberte roli (Demo):', en: 'Select Role (Demo):' },
  'footer.copyright': { cs: 'Fakulta mechatroniky, informatiky a mezioborových studií TUL.', en: 'Faculty of Mechatronics, Informatics and Interdisciplinary Studies TUL.' },

  // Enums
  'enum.WINTER': { cs: 'Zimní', en: 'Winter' },
  'enum.SUMMER': { cs: 'Letní', en: 'Summer' },
  'enum.TEAM': { cs: 'Týmový', en: 'Team' },
  'enum.INDIVIDUAL': { cs: 'Individuální', en: 'Individual' },

  // Course List & Detail
  'courseList.title': { cs: 'Seznam předmětů', en: 'Course List' },
  'courseList.subtitle': { cs: 'Prohlédněte si předměty vyučované na FM TUL.', en: 'Browse courses taught at FM TUL.' },
  'courseList.filter_by_lecturer': { cs: 'Předměty vyučujícího: ', en: 'Courses by lecturer: ' },
  'courseList.clear_filter': { cs: 'Zobrazit všechny předměty', en: 'Show all courses' },
  'courseList.no_courses': { cs: 'Nebyly nalezeny žádné předměty.', en: 'No courses found.' },
  'courseList.error_fetching': { cs: 'Nepodařilo se načíst seznam předmětů.', en: 'Failed to fetch courses.' },
  'courseDetail.syllabus': { cs: 'Sylabus předmětu', en: 'Course Syllabus' },
  'courseDetail.evaluation_criteria': { cs: 'Kritéria hodnocení', en: 'Evaluation Criteria' },
  'courseDetail.min_score': { cs: 'Minimum k splnění', en: 'Minimum to pass' },
  'courseDetail.points': { cs: 'bodů', en: 'points' },
  'courseDetail.lecturers': { cs: 'Vyučující', en: 'Lecturers' },
  'courseDetail.links': { cs: 'Užitečné odkazy', en: 'Useful Links' },
  'courseDetail.projects': { cs: 'Projekty předmětu', en: 'Course Projects' },
  'courseDetail.no_projects': { cs: 'Pro tento předmět zatím nejsou žádné projekty.', en: 'No projects for this course yet.' },
  'courseDetail.back_to_list': { cs: 'Zpět na seznam předmětů', en: 'Back to course list' },
  'courseDetail.error_fetching': { cs: 'Nepodařilo se načíst detail předmětu.', en: 'Failed to fetch course details.' },
  'courseDetail.not_found': { cs: 'Předmět nebyl nalezen.', en: 'Course not found.' },
  'courseDetail.view_detail': { cs: 'Detail předmětu', en: 'Course details' },
  'courseDetail.peer_bonus': { cs: 'Studentské peer-bonus body', en: 'Student peer-bonus points' },

  // Dashboard
  'dashboard.title': { cs: 'Prohlížeč projektů', en: 'Project Browser' },
  'dashboard.subtitle': { cs: 'Prozkoumejte inovativní práce studentů FM TUL.', en: 'Explore innovative work by FM TUL students.' },
  'dashboard.search_placeholder': { cs: 'Hledat projekt nebo technologii...', en: 'Search project or technology...' },
  'dashboard.filter_subject': { cs: 'Předmět', en: 'Subject' },
  'dashboard.filter_year': { cs: 'Akademický rok', en: 'Academic Year' },
  'dashboard.filter_technology': { cs: 'Technologie', en: 'Technology' },
  'dashboard.filter_lecturer': { cs: 'Vyučující', en: 'Lecturer' },
  'dashboard.all_subjects': { cs: 'Všechny předměty', en: 'All Subjects' },
  'dashboard.all_years': { cs: 'Všechny roky', en: 'All Years' },
  'dashboard.all_technologies': { cs: 'Všechny technologie', en: 'All Technologies' },
  'dashboard.all_lecturers': { cs: 'Všichni vyučující', en: 'All Lecturers' },
  'dashboard.no_results': { cs: 'Nebyly nalezeny žádné projekty', en: 'No projects found' },
  'dashboard.try_adjust': { cs: 'Zkuste upravit filtry nebo hledaný výraz.', en: 'Try adjusting filters or search query.' },
  'dashboard.clear_filters': { cs: 'Zrušit filtry', en: 'Clear Filters' },
  'dashboard.error_fetching': { cs: 'Nepodařilo se načíst projekty.', en: 'Failed to fetch projects.' },
  'dashboard.overview_title': { cs: 'Přehled všech projektů', en: 'All Projects Overview' },

  // Project Card & Modal
  'project.team': { cs: 'Řešitelský tým', en: 'Project Team' },
  'project.source_code': { cs: 'Zdrojový kód', en: 'Source Code' },
  'project.live_demo': { cs: 'Live Demo', en: 'Live Demo' },
  'project.back_to_projects': { cs: 'Zpět na projekty', en: 'Back to projects' },
  'project.no_description': { cs: 'Nebyl zadán žádný popis.', en: 'No description provided.' },
  'project.lecturer_links': { cs: 'Odkazy pro lektora', en: 'Lecturer links' },
  'project.student_links': { cs: 'Odkazy pro studenta', en: 'Student links' },
  'project.technologies': { cs: 'Použité technologie', en: 'Technologies' },
  'project.members': { cs: 'Členové týmu', en: 'Team Members' },
  'project.course_info': { cs: 'Informace o předmětu', en: 'Course Information' },
  'project.term': { cs: 'Semestr', en: 'Term' },
  'project.type': { cs: 'Typ projektu', en: 'Project Type' },
  'project.evaluate': { cs: 'Hodnotit projekt', en: 'Evaluate Project' },
  'project.view_results': { cs: 'Zobrazit výsledky', en: 'View Results' },

  // Project Detail page
  'projectDetail.title': { cs: 'Detail projektu', en: 'Project Detail' },
  'projectDetail.error_fetching': { cs: 'Nepodařilo se načíst detail projektu.', en: 'Failed to fetch project details.' },
  'projectDetail.not_found': { cs: 'Projekt nebyl nalezen.', en: 'Project not found.' },

  // Lecturer pages
  'lecturer.courseProjects.heading': { cs: 'Projekty předmětu', en: 'Course Projects' },
  'lecturer.projectEvaluation.title': { cs: 'Hodnocení projektu', en: 'Project Evaluation' },
  'lecturer.criterion': { cs: 'Kritérium', en: 'Criterion' },
  'lecturer.score': { cs: 'Body', en: 'Score' },

  // Student pages
  'student.results.title': { cs: 'Výsledky', en: 'Results' },
  'student.courseEvaluation.title': { cs: 'Hodnocení předmětu', en: 'Course Evaluation' },

  // Error / loading states
  'error.retry': { cs: 'Zkusit znovu', en: 'Retry' },
  
  // Admin Panel
  'admin.title': { cs: 'Administrace Lektora', en: 'Lecturer Administration' },
  'admin.subtitle': { cs: 'Spravujte předměty, projekty a prohlížejte hodnocení.', en: 'Manage subjects, projects, and view feedback.' },
  'admin.tab_project': { cs: 'Přidat Projekt', en: 'Add Project' },
  'admin.tab_subject': { cs: 'Přidat Předmět', en: 'Add Subject' },
  'admin.tab_feedback': { cs: 'Hodnocení', en: 'Feedback' },
  
  'form.project_title': { cs: 'Název projektu', en: 'Project Title' },
  'form.subject': { cs: 'Předmět', en: 'Subject' },
  'form.select_subject': { cs: 'Vyberte předmět...', en: 'Select subject...' },
  'form.short_desc': { cs: 'Krátký popis (max 150 znaků)', en: 'Short Description (max 150 chars)' },
  'form.full_desc': { cs: 'Detailní popis', en: 'Detailed Description' },
  'form.tags': { cs: 'Tagy (oddělené čárkou)', en: 'Tags (comma separated)' },
  'form.academic_year': { cs: 'Akademický rok', en: 'Academic Year' },
  'form.assign_students': { cs: 'Přiřadit studenty', en: 'Assign Students' },
  'form.manual_student': { cs: 'Přidat studenta ručně', en: 'Add Student Manually' },
  'form.name_placeholder': { cs: 'Jméno a příjmení', en: 'Name and Surname' },
  'form.email_placeholder': { cs: 'Email', en: 'Email' },
  'form.add': { cs: 'Přidat', en: 'Add' },
  'form.save_project': { cs: 'Uložit Projekt', en: 'Save Project' },
  'form.subject_code': { cs: 'Zkratka předmětu', en: 'Subject Code' },
  'form.subject_name': { cs: 'Název předmětu', en: 'Subject Name' },
  'form.success_subject': { cs: 'Předmět úspěšně přidán!', en: 'Subject successfully added!' },
  'form.success_project': { cs: 'Projekt úspěšně přidán!', en: 'Project successfully added!' },

  // Feedback
  'feedback.count_suffix': { cs: 'hodnocení', en: 'reviews' },
  'feedback.no_feedback': { cs: 'Zatím nebyla odeslána žádná hodnocení.', en: 'No feedback submitted yet.' },
  
  // Student Zone
  'student.zone_title': { cs: 'Studentská zóna', en: 'Student Zone' },
  'student.logged_as': { cs: 'Přihlášen jako', en: 'Logged in as' },
  'student.no_project': { cs: 'Nejste přiřazeni k žádnému projektu', en: 'You are not assigned to any project' },
  'student.contact_teacher': { cs: 'Kontaktujte svého vyučujícího pro přiřazení.', en: 'Contact your teacher for assignment.' },
  'student.my_team': { cs: 'Můj tým', en: 'My Team' },
  'student.active_project': { cs: 'Aktivní projekt', en: 'Active Project' },
  'student.team_members': { cs: 'Členové týmu', en: 'Team Members' },
  'student.click_evaluate': { cs: 'Klikněte pro hodnocení', en: 'Click to evaluate' },
  'student.alone': { cs: 'V tomto projektu jste sami.', en: 'You are alone in this project.' },
  'student.evaluating': { cs: 'Hodnotíte', en: 'Evaluating' },
  'student.select_colleague': { cs: 'Vyberte kolegu ze seznamu vlevo pro napsání hodnocení.', en: 'Select a colleague from the left list to write feedback.' },
  'student.strengths': { cs: 'Co dělá kolega dobře?', en: 'What does the colleague do well?' },
  'student.strengths_ph': { cs: 'Popište silné stránky, přínos pro tým...', en: 'Describe strengths, contribution to the team...' },
  'student.improvements': { cs: 'Prostor pro zlepšení', en: 'Areas for Improvement' },
  'student.improvements_ph': { cs: 'Kde vidíte rezervy, co by mohl dělat jinak...', en: 'Where do you see room for growth, what could be done differently...' },
  'student.disclaimer': { cs: 'Hodnocení je anonymní pro ostatní studenty, vidí ho pouze vyučující a adresát.', en: 'Feedback is anonymous to other students, visible only to the teacher and the recipient.' },
  'student.submit': { cs: 'Odeslat hodnocení', en: 'Submit Feedback' },
  'student.sent_history': { cs: 'Odeslaná hodnocení', en: 'Sent Feedback' },
  'student.for': { cs: 'Pro', en: 'For' },
  'student.label_strengths': { cs: 'Silné stránky', en: 'Strengths' },
  'student.label_improvements': { cs: 'Ke zlepšení', en: 'To Improve' },
  'student.success_sent': { cs: 'Hodnocení odesláno!', en: 'Feedback sent!' },
  'student.subject_eval': { cs: 'Hodnocení předmětu', en: 'Subject Evaluation' },
  'student.subject_strengths': { cs: 'Silné stránky předmětu', en: 'Subject Strengths' },
  'student.subject_improvements': { cs: 'Prostor ke zlepšení předmětu', en: 'Subject Areas for Improvement' },
  'student.peer_eval': { cs: 'Peer feedback (kolegové)', en: 'Peer Feedback (Colleagues)' },
  'student.points_allocation': { cs: 'Přidělení bodů', en: 'Points Allocation' },
  'student.points_remaining': { cs: 'Zbývající body', en: 'Remaining Points' },
  'student.avg_points': { cs: 'Průměrné peer body', en: 'Average Peer Points' },
  'student.received_feedback': { cs: 'Obdržená hodnocení od kolegů', en: 'Received Feedback from Colleagues' },
  'student.subject_feedback_title': { cs: 'Zpětná vazba na předmět', en: 'Subject Feedback' },
  'student.anonymous_notice': { cs: 'Hodnocení předmětu je anonymizované.', en: 'Subject evaluation is anonymized.' },
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider = ({ children }: { children: ReactNode }) => {
  const [language, setLanguage] = useState<Language>('cs');

  const t = (key: string) => {
    return translations[key]?.[language] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
