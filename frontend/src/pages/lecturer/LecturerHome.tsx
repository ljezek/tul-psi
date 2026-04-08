import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router';
import { BookOpen, Users, FolderOpen, AlertCircle, Plus } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { getCourses, createCourse, ApiError } from '@/api';
import { CourseListItem, UserRole, CourseCreate, CourseUpdate } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { CourseForm } from '@/components/admin/CourseForm';

export const LecturerHome = () => {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [courses, setCourses] = useState<CourseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Admin Create Course Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchCourses = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getCourses();
      setCourses(data);
    } catch (err) {
      if (err instanceof ApiError && typeof err.detail === 'string') {
        setError(err.detail);
      } else {
        setError(t('courseList.error_fetching'));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  const handleCreateCourse = async (data: CourseCreate | CourseUpdate) => {
    setFormLoading(true);
    setFormError(null);
    try {
      await createCourse(data as CourseCreate);
      setIsModalOpen(false);
      fetchCourses();
    } catch (err) {
      setFormError(err instanceof ApiError && typeof err.detail === 'string' ? err.detail : t('login.error_unexpected'));
    } finally {
      setFormLoading(false);
    }
  };

  const filteredCourses = useMemo(() => {
    if (!user) return [];
    if (user.role === UserRole.ADMIN) {
      return [...courses].sort((a, b) => a.code.localeCompare(b.code));
    }
    return courses.filter(course => course.lecturer_names.includes(user.name))
      .sort((a, b) => a.code.localeCompare(b.code));
  }, [courses, user]);

  if (loading) return <div className="py-20"><LoadingSpinner /></div>;
  if (error) return <div className="max-w-7xl mx-auto px-4 py-12"><ErrorMessage message={error} onRetry={fetchCourses} retryLabel={t('error.retry')} /></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8 animate-fade-in">
      {/* TODO: Add evaluation overview table (stretch goal) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <header>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2">
            {t('lecturer.title')}
          </h1>
          <div className="flex items-center gap-2 text-slate-500 font-medium">
            <div className="w-2 h-2 rounded-full bg-tul-blue animate-pulse" />
            {t('lecturer.subtitle')}
          </div>
        </header>
        {user?.role === UserRole.ADMIN && (
          <Button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2 shadow-lg shadow-tul-blue/20">
            <Plus size={18} />
            {t('admin.create_course')}
          </Button>
        )}
      </div>

      {filteredCourses.length === 0 ? (
        <div className="max-w-4xl mx-auto px-4 py-20 text-center">
          <div className="bg-white rounded-3xl p-12 shadow-xl shadow-slate-200/50 border border-slate-100">
            <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <BookOpen size={40} className="text-slate-300" />
            </div>
            <h2 className="text-2xl font-black text-slate-800 mb-2">{t('lecturer.no_courses')}</h2>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredCourses.map((course) => {
            return (
              <div
                key={course.id}
                className="group bg-white rounded-3xl border border-tul-blue/40 ring-1 ring-tul-blue/10 bg-tul-blue/[0.01] shadow-sm hover:shadow-xl hover:shadow-slate-200/50 hover:border-tul-blue/30 transition-all duration-300 overflow-hidden flex flex-col"
              >
                <div className="p-8 flex-grow space-y-6">
                  <div>
                    <span className="bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-100 text-[10px] font-black uppercase tracking-widest text-slate-500 group-hover:text-tul-blue group-hover:border-tul-blue/30 transition-colors inline-block mb-3">
                      {course.code}
                    </span>
                    <h3 className="text-2xl font-black text-slate-800 line-clamp-2">
                      {course.name}
                    </h3>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-start gap-2">
                      <Users size={16} className="text-slate-400 shrink-0 mt-0.5" />
                      <div className="text-sm font-bold text-slate-500 line-clamp-2">
                        {course.lecturer_names.join(', ') || '—'}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <FolderOpen size={16} className="text-slate-400 shrink-0" />
                      <div className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                        {t('lecturer.project_count')}: <span className="text-tul-blue ml-1">{course.stats.project_count}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <BookOpen size={16} className="text-slate-400 shrink-0" />
                      <div className="text-xs font-bold text-slate-400 uppercase tracking-widest truncate">
                        {t('lecturer.academic_years')}: <span className="text-slate-500 ml-1">{course.stats.academic_years.join(', ') || '—'}</span>
                      </div>
                    </div>

                    {course.stats.pending_evaluations_count !== undefined && course.stats.pending_evaluations_count !== null && course.stats.pending_evaluations_count > 0 && (
                      <div className="flex items-center gap-2 bg-amber-50 px-3 py-2 rounded-xl border border-amber-100 animate-pulse">
                        <AlertCircle size={16} className="text-amber-500 shrink-0" />
                        <div className="text-xs font-black text-amber-600 uppercase tracking-wider">
                          {t('lecturer.actions_requested')}: {course.stats.pending_evaluations_count}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="p-6 pt-0 mt-auto">
                  <Link
                    to={`/lecturer/course/${course.id}`}
                    className="block w-full text-center px-4 py-3 bg-slate-50 hover:bg-tul-blue hover:text-white text-tul-blue text-sm font-black rounded-xl transition-colors border border-slate-200 hover:border-tul-blue"
                  >
                    {t('lecturer.manage_projects')}
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Admin Create Course Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={t('admin.create_course')}
        size="xl"
      >
        <CourseForm
          onSubmit={handleCreateCourse}
          isLoading={formLoading}
          error={formError}
        />
      </Modal>
    </div>
  );
};
