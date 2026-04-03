import { useState, useEffect, useMemo } from 'react';
import { Search, BookOpen, Calendar, Tag, AlertCircle } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { getProjects, getCourses } from '@/api';
import { ProjectPublic, CourseListItem } from '@/types';
import { ProjectCard } from '@/components/ProjectCard';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

export const Dashboard = () => {
  const { t } = useLanguage();
  const [projects, setProjects] = useState<ProjectPublic[]>([]);
  const [courses, setCourses] = useState<CourseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCourse, setSelectedCourse] = useState('');
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedTech, setSelectedTech] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [projectsData, coursesData] = await Promise.all([
        getProjects(),
        getCourses()
      ]);
      setProjects(projectsData);
      setCourses(coursesData);
    } catch (err) {
      setError(t('dashboard.error_fetching') || 'Failed to fetch projects');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Extract distinct years and technologies for filters
  const years = useMemo(() => {
    const distinctYears = Array.from(new Set(projects.map(p => p.academic_year)));
    return distinctYears.sort((a, b) => b - a);
  }, [projects]);

  const technologies = useMemo(() => {
    const techSet = new Set<string>();
    projects.forEach(p => p.technologies.forEach(t => techSet.add(t)));
    return Array.from(techSet).sort();
  }, [projects]);

  // Client-side filtering
  const filteredProjects = useMemo(() => {
    return projects.filter(project => {
      const matchesSearch = 
        project.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (project.description?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false) ||
        project.technologies.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));
      
      const matchesCourse = selectedCourse === '' || project.course.code === selectedCourse;
      const matchesYear = selectedYear === '' || project.academic_year === parseInt(selectedYear);
      const matchesTech = selectedTech === '' || project.technologies.includes(selectedTech);

      return matchesSearch && matchesCourse && matchesYear && matchesTech;
    });
  }, [projects, searchQuery, selectedCourse, selectedYear, selectedTech]);

  if (loading) {
    return <div className="max-w-7xl mx-auto px-4 py-12"><LoadingSpinner className="h-64" /></div>;
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <ErrorMessage message={error} onRetry={fetchData} retryLabel={t('error.retry')} />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-10 text-center max-w-3xl mx-auto">
        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight mb-3">
          {t('dashboard.title')}
        </h1>
        <p className="text-lg text-slate-500">
          {t('dashboard.subtitle')}
        </p>
      </div>

      {/* Search and Filters */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Search Bar */}
          <div className="md:col-span-5 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Search size={20} />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue transition-all"
              placeholder={t('dashboard.search_placeholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Filters */}
          <div className="md:col-span-7 flex flex-wrap md:flex-nowrap gap-4">
            {/* Course Filter */}
            <div className="flex-1 min-w-[140px] relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <BookOpen size={16} />
              </div>
              <select
                className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue appearance-none transition-all"
                value={selectedCourse}
                onChange={(e) => setSelectedCourse(e.target.value)}
                aria-label={t('dashboard.filter_subject')}
              >
                <option value="">{t('dashboard.all_subjects')}</option>
                {courses.map(course => (
                  <option key={course.id} value={course.code}>
                    {course.code} - {course.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Year Filter */}
            <div className="flex-1 min-w-[140px] relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Calendar size={16} />
              </div>
              <select
                className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue appearance-none transition-all"
                value={selectedYear}
                onChange={(e) => setSelectedYear(e.target.value)}
                aria-label={t('dashboard.filter_year')}
              >
                <option value="">{t('dashboard.all_years')}</option>
                {years.map(year => (
                  <option key={year} value={year.toString()}>
                    {year}/{year + 1}
                  </option>
                ))}
              </select>
            </div>

            {/* Tech Filter */}
            <div className="flex-1 min-w-[140px] relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Tag size={16} />
              </div>
              <select
                className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue appearance-none transition-all"
                value={selectedTech}
                onChange={(e) => setSelectedTech(e.target.value)}
                aria-label={t('dashboard.filter_technology')}
              >
                <option value="">{t('dashboard.all_technologies')}</option>
                {technologies.map(tech => (
                  <option key={tech} value={tech}>
                    {tech}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Project Grid */}
      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredProjects.map(project => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      ) : (
        <div className="text-center py-24 bg-white rounded-2xl border border-dashed border-slate-200 shadow-inner">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-50 text-slate-400 mb-4">
            <AlertCircle size={32} />
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2">
            {t('dashboard.no_results')}
          </h3>
          <p className="text-slate-500 max-w-sm mx-auto">
            {t('dashboard.try_adjust')}
          </p>
          <button 
            onClick={() => { setSearchQuery(''); setSelectedCourse(''); setSelectedYear(''); setSelectedTech(''); }}
            className="mt-6 text-tul-blue font-bold hover:underline"
          >
            {t('dashboard.clear_filters')}
          </button>
        </div>
      )}
    </div>
  );
};
