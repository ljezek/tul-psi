import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, BookOpen, Calendar, Tag, AlertCircle, User } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { getProjects, getCourses, getCourse, updateCourse, ApiError } from '@/api';
import { ProjectPublic, CourseListItem, CourseDetail, CourseCreate, CourseUpdate } from '@/types';
import { ProjectCard } from '@/components/ProjectCard';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Modal } from '@/components/ui/Modal';
import { CourseForm } from '@/components/admin/CourseForm';

export const Dashboard = () => {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [projects, setProjects] = useState<ProjectPublic[]>([]);
  const [courses, setCourses] = useState<CourseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Edit Course Modal State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState<CourseDetail | null>(null);
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  // Filter states derived from URL
  const searchQuery = searchParams.get('q') || '';
  const selectedCourse = searchParams.get('course') || '';
  const selectedYear = searchParams.get('year') || '';
  const selectedTech = searchParams.get('tech') || '';
  const selectedLecturer = searchParams.get('lecturer') || '';

  const updateFilter = (key: string, value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, value);
    } else {
      newParams.delete(key);
    }
    setSearchParams(newParams, { replace: true });
  };

  const clearFilters = () => {
    setSearchParams({}, { replace: true });
  };

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
    } catch (_err) {
      setError(t('dashboard.error_fetching'));
      console.error(_err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [user]);

  const handleOpenEdit = async (courseId: number) => {
    try {
      setEditLoading(true);
      const detail = await getCourse(courseId);
      setEditingCourse(detail);
      setIsEditModalOpen(true);
    } catch (_err) {
      alert(t('courseDetail.error_fetching'));
    } finally {
      setEditLoading(false);
    }
  };

  const handleUpdateCourse = async (data: CourseCreate | CourseUpdate) => {
    if (!editingCourse) return;
    setEditLoading(true);
    setEditError(null);
    try {
      await updateCourse(editingCourse.id, data as CourseUpdate);
      setIsEditModalOpen(false);
      fetchData();
    } catch (_err) {
      setEditError(_err instanceof ApiError && typeof _err.detail === 'string' ? _err.detail : t('login.error_unexpected'));
    } finally {
      setEditLoading(false);
    }
  };

  // Extract distinct years, technologies, and lecturers for filters
  const years = useMemo(() => {
    const distinctYears = Array.from(new Set(projects.map(p => p.academic_year)));
    return distinctYears.sort((a, b) => b - a);
  }, [projects]);

  const technologies = useMemo(() => {
    const techSet = new Set<string>();
    projects.forEach(p => p.technologies.forEach(t => techSet.add(t)));
    return Array.from(techSet).sort();
  }, [projects]);

  const lecturers = useMemo(() => {
    const lecturerSet = new Set<string>();
    projects.forEach(p => p.course.lecturers.forEach(l => {
      if (l.name) lecturerSet.add(l.name);
    }));
    return Array.from(lecturerSet).sort();
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
      const matchesLecturer = selectedLecturer === '' || project.course.lecturers.some(l => l.name === selectedLecturer);

      return matchesSearch && matchesCourse && matchesYear && matchesTech && matchesLecturer;
    });
  }, [projects, searchQuery, selectedCourse, selectedYear, selectedTech, selectedLecturer]);

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
          <div className="md:col-span-12 lg:col-span-4 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Search size={20} />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue transition-all"
              placeholder={t('dashboard.search_placeholder')}
              aria-label={t('dashboard.search_placeholder')}
              value={searchQuery}
              onChange={(e) => updateFilter('q', e.target.value)}
            />
          </div>

          {/* Filters */}
          <div className="md:col-span-12 lg:col-span-8 flex flex-wrap gap-4">
            {/* Course Filter */}
            <div className="flex-1 min-w-[160px] relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <BookOpen size={16} />
              </div>
              <select
                className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue appearance-none transition-all"
                value={selectedCourse}
                onChange={(e) => updateFilter('course', e.target.value)}
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

            {/* Lecturer Filter */}
            <div className="flex-1 min-w-[160px] relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <User size={16} />
              </div>
              <select
                className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue appearance-none transition-all"
                value={selectedLecturer}
                onChange={(e) => updateFilter('lecturer', e.target.value)}
                aria-label={t('dashboard.filter_lecturer')}
              >
                <option value="">{t('dashboard.all_lecturers')}</option>
                {lecturers.map(name => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            </div>

            {/* Year Filter */}
            <div className="flex-1 min-w-[120px] relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Calendar size={16} />
              </div>
              <select
                className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue appearance-none transition-all"
                value={selectedYear}
                onChange={(e) => updateFilter('year', e.target.value)}
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
            <div className="flex-1 min-w-[160px] relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Tag size={16} />
              </div>
              <select
                className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue appearance-none transition-all"
                value={selectedTech}
                onChange={(e) => updateFilter('tech', e.target.value)}
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
            <ProjectCard key={project.id} project={project} onEditCourse={handleOpenEdit} />
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
            onClick={clearFilters}
            className="mt-6 text-tul-blue font-bold hover:underline"
          >
            {t('dashboard.clear_filters')}
          </button>
        </div>
      )}

      {/* Edit Course Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title={t('admin.edit_course')}
        size="xl"
      >
        <CourseForm
          initialData={editingCourse}
          onSubmit={handleUpdateCourse}
          isLoading={editLoading}
          error={editError}
        />
      </Modal>
    </div>
  );
};
