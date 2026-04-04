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
  'role.admin': { cs: 'Administrátor', en: 'Administrator' },
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
  'project.back_to_student_zone': { cs: 'Zpět do studentské zóny', en: 'Back to student zone' },
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
  'common.confirm_action': { cs: 'Jste si jisti? Tuto akci nelze vrátit zpět.', en: 'Are you sure? This cannot be undone.' },
  
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
  'student.disclaimer': { cs: 'Hodnocení je anonymní pro ostatní studenty. Vidí ho pouze vyučující a adresát. Své hodnocení můžete upravovat, dokud nebudou zveřejněny výsledky projektu (ke zveřejnění dojde po odevzdání hodnocení od všech studentů a lektorů).', en: 'Evaluation is anonymous to other students. It is only visible to the teacher and the recipient. You can edit your evaluation until the project results are unlocked (results are unlocked after all students and lecturers submit their evaluations).' },

  'student.submit': { cs: 'Odeslat hodnocení', en: 'Submit Feedback' },
  'student.sent_history': { cs: 'Odeslaná hodnocení', en: 'Sent Feedback' },
  'student.for': { cs: 'Pro', en: 'For' },
  'student.label_strengths': { cs: 'Silné stránky', en: 'Strengths' },
  'student.label_improvements': { cs: 'Ke zlepšení', en: 'To Improve' },
  'student.success_sent': { cs: 'Hodnocení odesláno!', en: 'Feedback sent!' },
  'student.course_eval': { cs: 'Hodnocení předmětu', en: 'Course Evaluation' },
  'student.course_strengths': { cs: 'Silné stránky předmětu', en: 'Course Strengths' },
  'student.course_strengths_ph': { cs: 'Co se vám na předmětu líbilo, co bylo přínosné...', en: 'What did you like about the course, what was beneficial...' },
  'student.course_improvements': { cs: 'Prostor ke zlepšení předmětu', en: 'Course Areas for Improvement' },
  'student.course_improvements_ph': { cs: 'Co byste na předmětu změnili, co vám nevyhovovalo...', en: 'What would you change about the course, what did not suit you...' },
  'student.peer_eval': { cs: 'Hodnocení týmu', en: 'Team Evaluation' },
  'student.peer_strengths': { cs: 'Silné stránky člena týmu', en: 'Teammate strengths' },
  'student.peer_improvements': { cs: 'Prostor ke zlepšení člena týmu', en: 'Teammate areas for improvement' },
  'student.points_allocation': { cs: 'Přidělení bodů', en: 'Points Allocation' },
  'student.points_remaining': { cs: 'Zbývající body', en: 'Remaining Points' },
  'student.points_budget': { cs: 'Celkem bodů k rozdělení', en: 'Total points to distribute' },
  'student.avg_points': { cs: 'Průměrné peer body', en: 'Average Peer Points' },
  'student.received_feedback': { cs: 'Obdržená hodnocení od kolegů', en: 'Received Feedback from Colleagues' },
  'student.subject_feedback_title': { cs: 'Zpětná vazba na předmět', en: 'Subject Feedback' },
  'student.anonymous_notice': { cs: 'Hodnocení je anonymní.', en: 'Evaluation is anonymous.' },
  'student.evaluation_status': { cs: 'Stav hodnocení', en: 'Evaluation Status' },
  'student.results_status': { cs: 'Stav výsledků', en: 'Results Status' },
  'student.submitted': { cs: 'Odesláno', en: 'Submitted' },
  'student.draft': { cs: 'Koncept', en: 'Draft' },
  'student.not_started': { cs: 'Nezahájeno', en: 'Not Started' },
  'student.results_available': { cs: 'Dostupné', en: 'Available' },
  'student.results_pending': { cs: 'Čeká se', en: 'Pending' },
  'student.submit_evaluation': { cs: 'Odevzdat hodnocení', en: 'Submit Evaluation' },
  'student.edit_evaluation': { cs: 'Upravit hodnocení', en: 'Edit Evaluation' },
  'student.view_prs': { cs: 'Zobrazit PR', en: 'View PRs' },
  'student.create_evaluation': { cs: 'Vytvořit hodnocení', en: 'Create evaluation' },
  'student.update_evaluation': { cs: 'Upravit hodnocení', en: 'Update evaluation' },
  'student.show_results': { cs: 'ZOBRAZIT VÝSLEDKY', en: 'SHOW RESULTS' },
  'student.lecturers': { cs: 'vyučující', en: 'lecturers' },
  'student.students': { cs: 'studenti', en: 'students' },
  'student.view_results': { cs: 'Zobrazit výsledky', en: 'View Results' },
  'student.points_must_total': { cs: 'Celkový počet bodů musí být přesně', en: 'Total points must be exactly' },
  'student.draft_saved': { cs: 'Koncept byl uložen.', en: 'Draft saved.' },
  'student.submit_success': { cs: 'Hodnocení bylo úspěšně uloženo.', en: 'Evaluation successfully saved.' },
  'student.submit_error': { cs: 'Odeslání se nezdařilo. Zkuste to prosím znovu.', en: 'Submission failed. Please try again.' },
  'student.unsaved_changes': { cs: 'Máte neuložené změny. Opravdu chcete odejít?', en: 'You have unsaved changes. Are you sure you want to leave?' },

  'label.points': { cs: 'bodů', en: 'points' },
  'label.min_required': { cs: 'minimum k splnění', en: 'minimum required' },
  // Results
  'results.title': { cs: 'Výsledky hodnocení', en: 'Evaluation Results' },
  'results.not_available': { cs: 'Výsledky zatím nejsou k dispozici.', en: 'Results are not available yet.' },
  'results.lecturer_eval': { cs: 'Hodnocení lektora', en: 'Lecturer Evaluation' },
  'results.peer_feedback': { cs: 'Týmové hodnocení', en: 'Team Evaluation' },
  'results.total_score': { cs: 'Celkem bodů', en: 'Total Points' },
  'results.avg_score': { cs: 'Body od vyučujících', en: 'Points from lecturers' },
  'results.avg_bonus': { cs: 'Body od kolegů', en: 'Points from teammates' },
  'results.min_required': { cs: 'Minimum k splnění', en: 'Min required points' },
  'results.verdict': { cs: 'Výsledek', en: 'Verdict' },
  'results.pass': { cs: 'SPLNĚNO', en: 'PASS' },
  'results.fail': { cs: 'NESPLNĚNO', en: 'FAIL' },
  'results.feedback': { cs: 'Hodnocení', en: 'Feedback' },

  // Login
  'login.title': { cs: 'Přihlášení', en: 'Login' },
  'login.email_label': { cs: 'Univerzitní email', en: 'University Email' },
  'login.email_placeholder': { cs: 'jan.novak@tul.cz', en: 'jan.novak@tul.cz' },
  'login.send_code': { cs: 'Odeslat kód', en: 'Send Code' },
  'login.email_info': { cs: 'Zadejte svůj @tul.cz email pro přihlášení.', en: 'Enter your @tul.cz email to sign in.' },
  'login.code_sent': { cs: 'Pokud účet existuje, kód byl odeslán na', en: 'If the account exists, a code was sent to' },
  'login.otp_label': { cs: 'Jednorázový kód', en: 'One-Time Code' },
  'login.otp_placeholder': { cs: '123456', en: '123456' },
  'login.verify': { cs: 'Ověřit', en: 'Verify' },
  'login.back': { cs: 'Zpět', en: 'Back' },
  'login.resend': { cs: 'Odeslat znovu', en: 'Resend Code' },
  'login.error_invalid_email': { cs: 'Zadejte platný @tul.cz email.', en: 'Enter a valid @tul.cz email.' },
  'login.error_invalid_otp': { cs: 'Neplatný nebo expirovaný kód.', en: 'Invalid or expired code.' },
  'login.error_too_many': { cs: 'Příliš mnoho pokusů — vyžádejte nový kód.', en: 'Too many attempts — request a new code.' },
  'login.error_unexpected': { cs: 'Došlo k nečekané chybě. Zkuste to prosím znovu.', en: 'An unexpected error occurred. Please try again.' },
  'login.otp_digit': { cs: 'Číslice {index} z 6', en: 'Digit {index} of 6' },

  // Profile
  'profile.title': { cs: 'Můj profil', en: 'My Profile' },
  'profile.role': { cs: 'Role', en: 'Role' },
  'profile.name': { cs: 'Jméno', en: 'Name' },
  'profile.github': { cs: 'GitHub alias', en: 'GitHub alias' },
  'profile.save': { cs: 'Uložit změny', en: 'Save Changes' },
  'profile.success': { cs: 'Profil byl úspěšně aktualizován.', en: 'Profile successfully updated.' },
  'profile.error_update': { cs: 'Nepodařilo se aktualizovat profil.', en: 'Failed to update profile.' },
  'profile.editing': { cs: 'Upravit profil', en: 'Edit Profile' },
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
