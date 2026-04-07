import { ReactNode } from 'react';
import { Calendar, User, BookOpen, ListChecks } from 'lucide-react';
import { Link } from 'react-router-dom';
import { CourseDetail } from '@/types';
import { useLanguage } from '@/contexts/LanguageContext';
import { MemberInfo } from '@/components/project/MemberInfo';

interface CourseHeroProps {
  course: CourseDetail;
  variant?: 'public' | 'lecturer';
  actions?: ReactNode;
  className?: string;
  showDetails?: boolean;
}

export const CourseHero = ({ 
  course, 
  variant = 'public', 
  actions,
  className = '',
  showDetails = false
}: CourseHeroProps) => {
  const { t } = useLanguage();
  const isLecturer = variant === 'lecturer';

  return (
    <div className={`bg-white rounded-3xl p-8 border border-slate-200/60 shadow-sm space-y-8 ${className}`}>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <Link 
            to={`/courses/${course.id}`}
            className="inline-block bg-tul-blue text-white px-3 py-1 rounded text-xs font-black uppercase tracking-widest hover:bg-blue-700 transition-colors mb-3"
          >
            {course.code}
          </Link>
          <h1 className={`${isLecturer ? 'text-3xl' : 'text-4xl'} font-black text-slate-900`}>{course.name}</h1>
          <div className="flex flex-wrap gap-4 mt-2 text-slate-500 font-bold text-sm">
            <span className="flex items-center gap-1.5">
              <Calendar size={16} className="text-slate-400" />
              {t(`enum.${course.term}`)}
            </span>
            <span className="text-slate-300">&bull;</span>
            <span>{t(`enum.${course.project_type}`)}</span>
            {!isLecturer && (
              <>
                <span className="text-slate-300">&bull;</span>
                <MemberInfo members={course.lecturers} variant="inline" />
              </>
            )}
            {isLecturer && (
              <>
                <span className="text-slate-300">&bull;</span>
                <span>{course.lecturers.map(l => l.name).join(', ')}</span>
              </>
            )}
          </div>
        </div>
        {actions && (
          <div className="flex gap-3">
            {actions}
          </div>
        )}
      </div>

      {!isLecturer && (
        <div className="flex flex-wrap gap-4">
          {course.lecturers.map((lecturer, idx) => (
            <div 
              key={idx} 
              className="flex flex-col gap-2 p-4 bg-white border border-slate-200 rounded-2xl shadow-sm hover:border-tul-blue transition-all"
            >
              <Link 
                to={`/courses?lecturer=${encodeURIComponent(lecturer.name)}`}
                className="flex items-center gap-2 text-slate-700 hover:text-tul-blue transition-colors group"
              >
                <User size={18} className="text-slate-400 group-hover:text-tul-blue" />
                <span className="font-bold">{lecturer.name}</span>
              </Link>
              <MemberInfo members={[lecturer]} variant="list" showLinks={true} className="!space-y-0" />
            </div>
          ))}
        </div>
      )}

      {showDetails && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-slate-100">
          <div className="space-y-4">
            <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
              <BookOpen size={16} className="text-tul-blue" />
              {t('courseDetail.syllabus')}
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">{course.syllabus || t('project.no_description')}</p>
            
            {course.links && course.links.length > 0 && (
              <div className="pt-2">
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{t('courseDetail.links')}</h4>
                <div className="flex flex-wrap gap-3">
                  {course.links.map((link, i) => (
                    <a key={i} href={link.url} target="_blank" rel="noopener noreferrer" className="text-xs font-bold text-tul-blue hover:underline flex items-center gap-1">
                      <BookOpen size={12} />
                      {link.label}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
              <ListChecks size={16} className="text-tul-blue" />
              {t('courseDetail.evaluation_criteria')}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {course.evaluation_criteria.map(c => (
                <div key={c.code} className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 leading-tight">{c.description}</div>
                  <div className="text-sm font-black text-slate-700">{c.max_score} {t('courseDetail.points')}</div>
                </div>
              ))}
              <div className="bg-tul-blue/[0.03] p-3 rounded-xl border border-tul-blue/10">
                <div className="text-[10px] font-black text-tul-blue/60 uppercase tracking-widest mb-1">{t('courseDetail.min_score')}</div>
                <div className="text-sm font-black text-tul-blue">{course.min_score} {t('courseDetail.points')}</div>
              </div>
              {course.peer_bonus_budget !== null && (
                <div className="bg-purple-50 p-3 rounded-xl border border-purple-100">
                  <div className="text-[10px] font-black text-purple-400 uppercase tracking-widest mb-1">{t('courseDetail.peer_bonus')}</div>
                  <div className="text-sm font-black text-purple-600">±{course.peer_bonus_budget} {t('courseDetail.points')}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
