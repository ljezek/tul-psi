import React, { useState, useMemo } from 'react';
import { Project, Subject, Student } from '../types';
import { ProjectCard } from './ProjectCard';
import { ProjectModal } from './ProjectModal';
import { Search, Filter, Layers } from 'lucide-react';
import { useLanguage } from '../LanguageContext';

interface DashboardProps {
  projects: Project[];
  subjects: Subject[];
  students: Student[];
}

export const Dashboard: React.FC<DashboardProps> = ({ projects, subjects, students }) => {
  const [selectedSubject, setSelectedSubject] = useState<string>('all');
  const [selectedYear, setSelectedYear] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const { t } = useLanguage();

  // Extract unique academic years
  const academicYears = useMemo(() => {
    const years = new Set(projects.map(p => p.academicYear));
    return Array.from(years).sort().reverse();
  }, [projects]);

  // Filter projects
  const filteredProjects = useMemo(() => {
    return projects.filter(project => {
      const matchesSubject = selectedSubject === 'all' || project.subjectId === selectedSubject;
      const matchesYear = selectedYear === 'all' || project.academicYear === selectedYear;
      const matchesSearch = project.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                            project.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
      
      return matchesSubject && matchesYear && matchesSearch;
    });
  }, [projects, selectedSubject, selectedYear, searchQuery]);

  const getAuthors = (project: Project) => {
    return students.filter(s => project.authorIds.includes(s.id));
  };

  const getSubject = (project: Project) => {
    return subjects.find(s => s.id === project.subjectId);
  };

  return (
    <div className="space-y-8">
      {/* Header & Filters */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{t('dashboard.title')}</h1>
            <p className="text-slate-500">{t('dashboard.subtitle')}</p>
          </div>
          <div className="relative w-full md:w-auto">
            <input 
              type="text" 
              placeholder={t('dashboard.search_placeholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 w-full md:w-64 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
            <Search className="absolute left-3 top-2.5 text-slate-400" size={18} />
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 border-t border-slate-100 pt-4">
          <div className="flex-1">
            <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">{t('dashboard.filter_subject')}</label>
            <div className="relative">
              <select 
                value={selectedSubject} 
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="w-full appearance-none bg-slate-50 border border-slate-200 text-slate-700 py-2 px-3 pr-8 rounded leading-tight focus:outline-none focus:bg-white focus:border-blue-500"
              >
                <option value="all">{t('dashboard.all_subjects')}</option>
                {subjects.map(s => (
                  <option key={s.id} value={s.id}>{s.name} ({s.code})</option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-700">
                <Filter size={14} />
              </div>
            </div>
          </div>

          <div className="flex-1">
            <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">{t('dashboard.filter_year')}</label>
            <div className="relative">
              <select 
                value={selectedYear} 
                onChange={(e) => setSelectedYear(e.target.value)}
                className="w-full appearance-none bg-slate-50 border border-slate-200 text-slate-700 py-2 px-3 pr-8 rounded leading-tight focus:outline-none focus:bg-white focus:border-blue-500"
              >
                <option value="all">{t('dashboard.all_years')}</option>
                {academicYears.map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-700">
                <Layers size={14} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Grid */}
      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map(project => (
            <ProjectCard 
              key={project.id} 
              project={project} 
              subject={getSubject(project)}
              authors={getAuthors(project)}
              onClick={() => setActiveProject(project)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-300">
          <div className="mx-auto w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mb-4">
            <Search className="text-slate-400" />
          </div>
          <h3 className="text-lg font-medium text-slate-900">{t('dashboard.no_results')}</h3>
          <p className="text-slate-500">{t('dashboard.try_adjust')}</p>
        </div>
      )}

      {/* Modal Detail */}
      <ProjectModal 
        project={activeProject}
        subject={activeProject ? getSubject(activeProject) : undefined}
        authors={activeProject ? getAuthors(activeProject) : []}
        isOpen={!!activeProject}
        onClose={() => setActiveProject(null)}
      />
    </div>
  );
};