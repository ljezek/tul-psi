import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router';
import { BookOpen, Users, FolderOpen, AlertCircle } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { getCourses, ApiError } from '@/api';
import { CourseListItem } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

import { CourseCard } from '@/components/course/CourseCard';

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

  const filteredCourses = useMemo(() => {
    if (!user) return [];
    return courses.filter(course => course.lecturer_names.includes(user.name))
      .sort((a, b) => a.code.localeCompare(b.code));
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
          {filteredCourses.map((course) => (
            <CourseCard
              key={course.id}
              course={course}
              href={`/lecturer/course/${course.id}`}
              variant="lecturer"
              footer={
                <div className="p-6 pt-0 mt-auto">
                  <Link
                    to={`/lecturer/course/${course.id}`}
                    className="block w-full text-center px-4 py-3 bg-slate-50 hover:bg-tul-blue hover:text-white text-tul-blue text-sm font-black rounded-xl transition-colors border border-slate-200 hover:border-tul-blue"
                  >
                    {t('lecturer.manage_projects')}
                  </Link>
                </div>
              }
            >
              {course.stats.pending_evaluations_count !== undefined && course.stats.pending_evaluations_count !== null && course.stats.pending_evaluations_count > 0 && (
                <div className="flex items-center gap-2 bg-amber-50 px-3 py-2 rounded-xl border border-amber-100 animate-pulse">
                  <AlertCircle size={16} className="text-amber-500 shrink-0" />
                  <div className="text-xs font-black text-amber-600 uppercase tracking-wider">
                    {t('lecturer.actions_requested')}: {course.stats.pending_evaluations_count}
                  </div>
                </div>
              )}
            </CourseCard>
          ))}
        </div>
      )}
    </div>
  );
};
