import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router';
import { BookOpen, Users, FolderOpen } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { getCourses, ApiError } from '@/api';
import { CourseListItem } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

export const LecturerHome = () => {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [courses, setCourses] = useState<CourseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const sortedCourses = useMemo(() => {
    if (!user) return courses;
    return [...courses].sort((a, b) => {
      const aIsLecturer = a.lecturer_names.includes(user.name);
      const bIsLecturer = b.lecturer_names.includes(user.name);
      if (aIsLecturer && !bIsLecturer) return -1;
      if (!aIsLecturer && bIsLecturer) return 1;
      return a.code.localeCompare(b.code);
    });
  }, [courses, user]);

  if (loading) return <div className="py-20"><LoadingSpinner /></div>;
  if (error) return <div className="max-w-7xl mx-auto px-4 py-12"><ErrorMessage message={error} onRetry={fetchCourses} retryLabel={t('error.retry')} /></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* TODO: Add evaluation overview table (stretch goal) */}
      <header className="mb-12">
        <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2">
          {t('lecturer.title')}
        </h1>
        <div className="flex items-center gap-2 text-slate-500 font-medium">
          <div className="w-2 h-2 rounded-full bg-tul-blue animate-pulse" />
          {t('lecturer.subtitle')}
        </div>
      </header>

      {sortedCourses.length === 0 ? (
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
          {sortedCourses.map((course) => {
            const isLecturer = user && course.lecturer_names.includes(user.name);
            return (
              <div
                key={course.id}
                className={`group bg-white rounded-3xl border shadow-sm hover:shadow-xl hover:shadow-slate-200/50 hover:border-tul-blue/30 transition-all duration-300 overflow-hidden flex flex-col ${
                  isLecturer ? 'border-tul-blue/40 ring-1 ring-tul-blue/10 bg-tul-blue/[0.01]' : 'border-slate-200/60'
                }`}
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
    </div>
  );
};
