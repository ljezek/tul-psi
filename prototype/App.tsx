import React, { useState } from 'react';
import { Project, Subject, Role, Feedback, Student } from './types';
import { MOCK_PROJECTS, MOCK_SUBJECTS, MOCK_STUDENTS, MOCK_FEEDBACKS, CURRENT_STUDENT_ID } from './mockData';
import { Dashboard } from './components/Dashboard';
import { AdminPanel } from './components/AdminPanel';
import { StudentZone } from './components/StudentZone';
import { Shield, GraduationCap, LayoutGrid, Menu, X, Globe } from 'lucide-react';
import { LanguageProvider, useLanguage } from './LanguageContext';

const AppContent: React.FC = () => {
  // Global State
  const [role, setRole] = useState<Role>('host');
  const [projects, setProjects] = useState<Project[]>(MOCK_PROJECTS);
  const [subjects, setSubjects] = useState<Subject[]>(MOCK_SUBJECTS);
  const [feedbacks, setFeedbacks] = useState<Feedback[]>(MOCK_FEEDBACKS);
  const [students, setStudents] = useState<Student[]>(MOCK_STUDENTS);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const { t, language, setLanguage } = useLanguage();

  // Handlers
  const handleAddSubject = (subject: Subject) => {
    setSubjects([...subjects, subject]);
  };

  const handleAddProject = (project: Project) => {
    setProjects([project, ...projects]);
  };

  const handleAddStudent = (student: Student) => {
    setStudents([...students, student]);
  };

  const handleAddFeedback = (feedback: Feedback) => {
    setFeedbacks([...feedbacks, feedback]);
  };

  const toggleLanguage = () => {
    setLanguage(language === 'cs' ? 'en' : 'cs');
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Navigation Bar */}
      <nav className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-white/20 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="bg-tul-blue w-8 h-8 rounded flex items-center justify-center text-white font-bold">
                FM
              </div>
              <span className="text-xl font-bold text-slate-800 tracking-tight">
                {language === 'cs' ? 'Katalog' : 'Project'} <span className="text-tul-blue">{language === 'cs' ? 'Projektů' : 'Catalog'}</span>
              </span>
            </div>

            {/* Desktop Role Switcher & Language */}
            <div className="hidden md:flex items-center gap-4">
               <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg">
                <button
                    onClick={() => setRole('host')}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${role === 'host' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'}`}
                >
                    <div className="flex items-center gap-2">
                    <LayoutGrid size={14} /> {t('role.public')}
                    </div>
                </button>
                <button
                    onClick={() => setRole('student')}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${role === 'student' ? 'bg-white text-tul-blue shadow-sm' : 'text-slate-500 hover:text-slate-900'}`}
                >
                    <div className="flex items-center gap-2">
                    <GraduationCap size={14} /> {t('role.student')}
                    </div>
                </button>
                <button
                    onClick={() => setRole('lektor')}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${role === 'lektor' ? 'bg-white text-purple-600 shadow-sm' : 'text-slate-500 hover:text-slate-900'}`}
                >
                    <div className="flex items-center gap-2">
                    <Shield size={14} /> {t('role.lecturer')}
                    </div>
                </button>
               </div>

               <button 
                 onClick={toggleLanguage}
                 className="flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-tul-blue transition-colors px-2 py-1"
               >
                 <Globe size={18} />
                 <span>{language.toUpperCase()}</span>
               </button>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden flex items-center gap-4">
              <button 
                 onClick={toggleLanguage}
                 className="flex items-center gap-1 text-sm font-bold text-slate-600"
               >
                 {language.toUpperCase()}
               </button>
              <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="p-2 text-slate-600">
                {mobileMenuOpen ? <X /> : <Menu />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Role Switcher */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-t border-slate-200 p-4 space-y-2">
            <p className="text-xs text-slate-500 uppercase font-semibold mb-2">{t('role.select_demo')}</p>
            <button onClick={() => { setRole('host'); setMobileMenuOpen(false); }} className="w-full text-left px-4 py-2 rounded bg-slate-50 text-slate-700">{t('role.public')}</button>
            <button onClick={() => { setRole('student'); setMobileMenuOpen(false); }} className="w-full text-left px-4 py-2 rounded bg-slate-50 text-slate-700">{t('role.student')}</button>
            <button onClick={() => { setRole('lektor'); setMobileMenuOpen(false); }} className="w-full text-left px-4 py-2 rounded bg-slate-50 text-slate-700">{t('role.lecturer')}</button>
          </div>
        )}
      </nav>

      {/* Main Content Area */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {role === 'host' && (
          <Dashboard 
            projects={projects} 
            subjects={subjects} 
            students={students} 
          />
        )}

        {role === 'lektor' && (
          <AdminPanel 
            subjects={subjects} 
            students={students}
            projects={projects}
            feedbacks={feedbacks}
            onAddSubject={handleAddSubject}
            onAddProject={handleAddProject}
            onAddStudent={handleAddStudent}
          />
        )}

        {role === 'student' && (
          <div className="space-y-8">
            <div className="bg-blue-600 text-white p-6 rounded-2xl shadow-lg relative overflow-hidden">
              <div className="absolute right-0 top-0 opacity-10 transform translate-x-10 -translate-y-10">
                <GraduationCap size={200} />
              </div>
              <div className="relative z-10">
                <h1 className="text-2xl font-bold mb-1">{t('student.zone_title')}</h1>
                <p className="text-blue-100">{t('student.logged_as')}: {students.find(s => s.id === CURRENT_STUDENT_ID)?.name}</p>
              </div>
            </div>

            <StudentZone 
              currentStudentId={CURRENT_STUDENT_ID}
              projects={projects}
              students={students}
              feedbacks={feedbacks}
              onAddFeedback={handleAddFeedback}
            />

            {/* Students can also see the dashboard below their zone */}
            <div className="pt-8 border-t border-slate-200">
               <h3 className="text-xl font-bold text-slate-800 mb-6">{t('dashboard.overview_title')}</h3>
               <Dashboard 
                  projects={projects} 
                  subjects={subjects} 
                  students={students} 
                />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-8 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-slate-500 text-sm">
            © {new Date().getFullYear()} {t('footer.copyright')}
          </p>
          <p className="text-slate-400 text-xs mt-2">
            Technická univerzita v Liberci | Studentská 1402/2 | 461 17 Liberec 1
          </p>
        </div>
      </footer>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  );
};

export default App;