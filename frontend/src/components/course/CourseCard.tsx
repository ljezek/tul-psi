import { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, User, ArrowRight } from 'lucide-react';
import { CourseListItem } from '@/types';
import { useLanguage } from '@/contexts/LanguageContext';

interface CourseCardProps {
  course: CourseListItem;
  href: string;
  footer?: ReactNode;
  variant?: 'public' | 'lecturer';
  className?: string;
  children?: ReactNode; // Extra content below course name (like alerts)
}

export const CourseCard = ({ 
  course, 
  href, 
  footer, 
  variant = 'public',
  className = '',
  children
}: CourseCardProps) => {
  const { t } = useLanguage();

  const isLecturer = variant === 'lecturer';

  const baseStyles = isLecturer 
    ? "group bg-white rounded-3xl border border-tul-blue/40 ring-1 ring-tul-blue/10 bg-tul-blue/[0.01] shadow-sm hover:shadow-xl hover:shadow-slate-200/50 hover:border-tul-blue/30 transition-all duration-300 overflow-hidden flex flex-col"
    : "bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md hover:border-tul-blue/20 transition-all group flex flex-col h-full";

  const content = (
    <>
      <div className={`flex items-start justify-between ${isLecturer ? 'mb-0' : 'mb-4'}`}>
        <span className={`${isLecturer ? 'bg-slate-50 border border-slate-100' : 'bg-tul-blue/10'} px-2 py-1 text-tul-blue text-xs font-bold rounded uppercase tracking-wider transition-colors`}>
          {course.code}
        </span>
        <span className="text-xs text-slate-400 font-medium">
          {course.stats.project_count} {t('lecturer.project_count')}
        </span>
      </div>
      
      <h3 className={`font-black text-slate-800 ${isLecturer ? 'text-2xl line-clamp-2' : 'text-xl mb-3 group-hover:text-tul-blue'} transition-colors`}>
        {course.name}
      </h3>
      
      <div className={`space-y-3 ${isLecturer ? 'mt-6' : 'mb-6 flex-grow'}`}>
        <div className="flex items-start gap-2 text-slate-500 text-sm">
          <User size={16} className="text-slate-400 shrink-0 mt-0.5" />
          <span className={`font-bold ${isLecturer ? 'line-clamp-2' : 'line-clamp-1'}`}>
            {course.lecturer_names.join(', ') || '—'}
          </span>
        </div>
        <div className="flex items-center gap-2 text-slate-500 text-sm">
          <BookOpen size={16} className="text-slate-400 shrink-0" />
          <span className={isLecturer ? 'text-xs font-bold text-slate-400 uppercase tracking-widest truncate' : ''}>
            {isLecturer ? `${t('lecturer.academic_years')}: ` : ''}
            <span className={isLecturer ? 'text-slate-500 ml-1' : ''}>
              {course.stats.academic_years.join(', ') || '—'}
            </span>
          </span>
        </div>
        {children}
      </div>

      {!isLecturer && !footer && (
        <div className="pt-4 border-t border-slate-50 flex items-center text-tul-blue text-sm font-bold mt-auto">
          {t('courseDetail.view_detail')}
          <ArrowRight size={16} className="ml-2 group-hover:translate-x-1 transition-transform" />
        </div>
      )}
      
      {footer}
    </>
  );

  if (isLecturer) {
    return (
      <div className={`${baseStyles} ${className}`}>
        <div className="p-8 flex-grow space-y-6">
          {content}
        </div>
      </div>
    );
  }

  return (
    <Link to={href} className={`${baseStyles} ${className}`}>
      {content}
    </Link>
  );
};
