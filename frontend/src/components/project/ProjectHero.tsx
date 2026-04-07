import { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Calendar } from 'lucide-react';
import { ProjectPublic } from '@/types';
import { useLanguage } from '@/contexts/LanguageContext';

interface ProjectHeroProps {
  project: ProjectPublic;
  backLink?: { to: string; label: string };
  rightContent?: ReactNode;
  bottomContent?: ReactNode;
  className?: string;
}

export const ProjectHero = ({ 
  project, 
  backLink, 
  rightContent, 
  bottomContent,
  className = '' 
}: ProjectHeroProps) => {
  const { t } = useLanguage();

  return (
    <div className={`space-y-8 ${className}`}>
      {/* Back Link */}
      {backLink && (
        <Link 
          to={backLink.to} 
          className="inline-flex items-center gap-2 text-sm font-bold text-slate-400 hover:text-tul-blue transition-colors group"
        >
          <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
          {backLink.label}
        </Link>
      )}

      {/* Header Card */}
      <div className="bg-white p-8 rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 flex flex-col md:flex-row justify-between gap-8">
        <div className="space-y-6 flex-1">
          <div>
            <div className="flex flex-wrap items-center gap-3 mb-4">
              <Link 
                to={`/courses/${project.course.id}`}
                className="px-3 py-1 bg-tul-blue text-white text-[10px] font-black uppercase tracking-widest rounded hover:bg-blue-700 transition-colors"
              >
                {project.course.code}
              </Link>
              <Link 
                to={`/courses/${project.course.id}`}
                className="text-slate-500 font-bold hover:text-tul-blue transition-colors text-sm"
              >
                {project.course.name}
              </Link>
              <span className="h-4 w-px bg-slate-200 mx-1 hidden sm:block"></span>
              <span className="flex items-center gap-1.5 text-slate-400 font-bold text-xs uppercase tracking-widest">
                <Calendar size={14} className="text-slate-300" />
                {project.academic_year}/{project.academic_year + 1}
              </span>
            </div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tight leading-tight">
              {project.title}
            </h1>
            {bottomContent && <div className="mt-6 pt-6 border-t border-slate-50">{bottomContent}</div>}
          </div>
        </div>

        {rightContent && (
          <div className="flex items-center gap-8 bg-slate-50/50 p-6 rounded-2xl border border-slate-100 h-fit self-center">
            {rightContent}
          </div>
        )}
      </div>
    </div>
  );
};
