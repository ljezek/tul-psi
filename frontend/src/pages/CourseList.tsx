import { useState, useEffect, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Info, Search } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { getCourses } from '@/api';
import { CourseListItem } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Button } from '@/components/ui/Button';

import { CourseCard } from '@/components/course/CourseCard';

export const CourseList = () => {
  const { t } = useLanguage();
  const [searchParams] = useSearchParams();
  const lecturerFilter = searchParams.get('lecturer');

  const [courses, setCourses] = useState<CourseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchQuery] = useState('');

  const fetchCourses = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getCourses();
      setCourses(data);
    } catch (err) {
      setError(t('courseList.error_fetching'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  const filteredCourses = useMemo(() => {
    return courses.filter(course => {
      const matchesLecturer = !lecturerFilter || course.lecturer_names.includes(lecturerFilter);
      const matchesSearch = !searchTerm || 
        course.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
        course.code.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesLecturer && matchesSearch;
    });
  }, [courses, lecturerFilter, searchTerm]);

  if (loading) {
    return <div className="max-w-7xl mx-auto px-4 py-12"><LoadingSpinner className="h-64" /></div>;
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <ErrorMessage message={error} onRetry={fetchCourses} retryLabel={t('error.retry')} />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight mb-3">
          {t('courseList.title')}
        </h1>
        <p className="text-lg text-slate-500">
          {t('courseList.subtitle')}
        </p>
      </div>

      {/* Active Filters Info */}
      {(lecturerFilter || searchTerm) && (
        <div className="bg-tul-blue/5 border border-tul-blue/10 rounded-xl p-4 mb-8 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-tul-blue">
            <Info size={20} />
            <span className="font-medium">
              {lecturerFilter && (
                <>
                  {t('courseList.filter_by_lecturer')}
                  <span className="font-bold underline">{lecturerFilter}</span>
                </>
              )}
              {lecturerFilter && searchTerm && ' + '}
              {searchTerm && (
                <>
                  {t('dashboard.search_placeholder')}: 
                  <span className="font-bold"> "{searchTerm}"</span>
                </>
              )}
            </span>
          </div>
          <Link to="/courses">
            <Button variant="outline" size="sm" onClick={() => setSearchQuery('')}>
              {t('courseList.clear_filter')}
            </Button>
          </Link>
        </div>
      )}

      {/* Internal Search */}
      <div className="mb-8 relative max-w-md">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
          <Search size={20} />
        </div>
        <input
          type="text"
          className="block w-full pl-10 pr-3 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 focus:border-tul-blue transition-all shadow-sm"
          placeholder={t('dashboard.search_placeholder')}
          aria-label={t('dashboard.search_placeholder')}
          value={searchTerm}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Course Grid */}
      {filteredCourses.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCourses.map(course => (
            <CourseCard 
              key={course.id} 
              course={course} 
              href={`/courses/${course.id}`} 
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-24 bg-white rounded-2xl border border-dashed border-slate-200">
          <p className="text-slate-500">{t('courseList.no_courses')}</p>
        </div>
      )}
    </div>
  );
};
