import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { ExternalLink, Users, Tag, Settings } from 'lucide-react';
import { GitHubLogo } from '@/components/icons/GitHubLogo';
import { ProjectPublic, UserRole } from '@/types';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { isSafeUrl } from '@/utils/url';
import { CourseEvaluationStatusCard } from '@/components/student/CourseEvaluationStatusCard';

export interface ProjectCardProps {
  project: ProjectPublic;
  onEditProject?: (projectId: number) => void;
}

export const ProjectCard = ({ project, onEditProject }: ProjectCardProps) => {
  const { t } = useLanguage();
  const { user } = useAuth();

  const isMember = project.members.some(m => m.id === user?.id);
  const isCourseOwner = project.course.lecturers.some(l => l.email === user?.email);
  const canEditProject = user?.role === UserRole.ADMIN || isCourseOwner || isMember;

  // Truncate members list
  const memberNames = project.members.map(m => m.name.split(' ')[0]);
  const displayedMembers = memberNames.slice(0, 3).join(', ') + (memberNames.length > 3 ? '...' : '');

  return (
    <div className="relative bg-white dark:bg-slate-800 rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden border border-slate-100 dark:border-slate-700 flex flex-col h-full group">
      {/* Primary stretched link covering the whole card for keyboard/screen-reader navigation. */}
      <Link
        to={`/projects/${project.id}`}
        className="absolute inset-0 z-0"
        aria-label={project.title}
      />

      {/* Header Area */}
      <div className="p-4 flex justify-between items-start gap-2 relative z-10 pointer-events-none">
        <div className="flex gap-2 items-center pointer-events-auto">
          <Link
            to={`/courses/${project.course.id}`}
            className="px-2 py-1 bg-fm-orange/10 text-fm-orange text-xs font-bold rounded uppercase tracking-wider hover:bg-fm-orange/20 transition-colors"
          >
            {project.course.code}
          </Link>
          {canEditProject && onEditProject && (
            <button
              onClick={(e) => {
                e.preventDefault();
                onEditProject(project.id);
              }}
              className="p-1 text-slate-400 hover:text-fm-orange hover:bg-slate-100 rounded-lg transition-all"
              title={t('admin.edit_project')}
            >
              <Settings size={14} />
            </button>
          )}
        </div>
        <span className="px-2 py-1 bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 text-xs font-medium rounded">
          {project.academic_year}/{project.academic_year + 1}
        </span>
      </div>

      {/* Content */}
      <div className="px-4 pb-4 flex-grow relative z-10 pointer-events-none">
        <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-2 group-hover:text-fm-orange transition-colors">
          {project.title}
        </h3>
        <div className="text-slate-600 dark:text-slate-400 text-sm line-clamp-2 mb-4 prose-compact">
          {project.description ? (
            <ReactMarkdown>{project.description}</ReactMarkdown>
          ) : (
            t('project.no_description')
          )}
        </div>

        {/* Technologies */}
        <div className="flex flex-wrap gap-1 mb-4">
          <Tag size={14} className="text-slate-400 mr-1" />
          {project.technologies.slice(0, 3).map((tech, idx) => (
            <span 
              key={idx} 
              className="px-2 py-0.5 bg-slate-50 dark:bg-slate-700 text-slate-500 dark:text-slate-400 text-[10px] font-semibold rounded-full border border-slate-100 dark:border-slate-600 uppercase"
            >
              {tech}
            </span>
          ))}
          {project.technologies.length > 3 && (
            <span className="text-[10px] font-semibold text-slate-400 self-center">
              +{project.technologies.length - 3}
            </span>
          )}
        </div>

        {/* Evaluation Status for Members */}
        {isMember && (
          <CourseEvaluationStatusCard 
            project={project}
            user={user}
            isCompact={true}
            className="pt-3 border-t border-slate-50 pointer-events-auto"
          />
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-slate-50 dark:bg-slate-700 border-t border-slate-100 dark:border-slate-600 flex justify-between items-center mt-auto relative z-10 pointer-events-none">
        <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs font-medium">
          <Users size={14} />
          <span>{displayedMembers}</span>
        </div>
        
        <div className="flex items-center gap-3 pointer-events-auto">
          {project.github_url && isSafeUrl(project.github_url) && (
            <a
              href={project.github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-slate-800 transition-colors"
              title={t('project.source_code')}
            >
              <GitHubLogo size={18} />
            </a>
          )}
          {project.live_url && isSafeUrl(project.live_url) && (
            <a
              href={project.live_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-fm-orange transition-colors"
              title={t('project.live_demo')}
            >
              <ExternalLink size={18} />
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
