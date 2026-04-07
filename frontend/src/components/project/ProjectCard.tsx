import { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { Users, Calendar, Globe } from 'lucide-react';
import { GitHubLogo } from '@/components/icons/GitHubLogo';
import { ProjectPublic } from '@/types';
import { useLanguage } from '@/contexts/LanguageContext';
import { MemberInfo } from './MemberInfo';

interface ProjectCardProps {
  project: ProjectPublic;
  href?: string;
  className?: string;
  headerActions?: ReactNode;
  children?: ReactNode; // Main content slot
  footer?: ReactNode;
  showCourseBadge?: boolean;
  showLinks?: boolean;
  variant?: 'default' | 'lecturer';
}

export const ProjectCard = ({ 
  project, 
  href, 
  className = '', 
  headerActions,
  children,
  footer,
  showCourseBadge = true,
  showLinks = true,
  variant = 'default'
}: ProjectCardProps) => {
  const { t } = useLanguage();

  const isLecturer = variant === 'lecturer';

  const cardContent = (
    <div className={`group bg-white rounded-3xl border border-slate-200/60 shadow-sm hover:shadow-xl hover:shadow-slate-200/50 hover:border-tul-blue/30 transition-all duration-300 overflow-hidden flex flex-col ${isLecturer ? 'md:flex-row' : ''} ${className}`}>
      <div className="flex-1 p-8">
        <div className="flex justify-between items-start mb-4">
          <div className="flex gap-2">
            {showCourseBadge && (
              <Link 
                to={`/courses/${project.course.id}`}
                className="bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-100 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-tul-blue hover:border-tul-blue/30 transition-colors"
              >
                {project.course.code}
              </Link>
            )}
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 rounded-xl border border-slate-100 text-[10px] font-black text-slate-400 uppercase tracking-widest">
              <Calendar size={12} />
              {project.academic_year}
            </div>
          </div>
          {headerActions}
        </div>

        {href ? (
          <Link to={href} className="block group/title">
            <h3 className="text-2xl font-black text-slate-800 mb-2 group-hover/title:text-tul-blue transition-colors line-clamp-2">
              {project.title}
            </h3>
          </Link>
        ) : (
          <h3 className="text-2xl font-black text-slate-800 mb-2 transition-colors line-clamp-2">
            {project.title}
          </h3>
        )}

        {/* Team Members */}
        <div className="flex items-center gap-2 mb-4">
          <Users size={14} className="text-slate-400" />
          <MemberInfo members={project.members} variant="inline" className="text-slate-500" />
        </div>

        {/* External Links */}
        {showLinks && (project.github_url || project.live_url) && (
          <div className="flex gap-4 mb-6">
            {project.github_url && (
              <a 
                href={project.github_url} 
                target="_blank" 
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-black text-slate-400 hover:text-slate-900 transition-colors uppercase tracking-wider"
              >
                <GitHubLogo size={14} />
                {t('common.repo')}
              </a>
            )}
            {project.live_url && (
              <a 
                href={project.live_url} 
                target="_blank" 
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-black text-slate-400 hover:text-slate-900 transition-colors uppercase tracking-wider"
              >
                <Globe size={14} />
                {t('common.app')}
              </a>
            )}
          </div>
        )}

        {children}
        {footer}
      </div>
    </div>
  );

  return cardContent;
};
