import { MouseEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Code, ExternalLink, Users, Tag } from 'lucide-react';
import { ProjectPublic } from '@/types';
import { useLanguage } from '@/contexts/LanguageContext';

export interface ProjectCardProps {
  project: ProjectPublic;
}

export const ProjectCard = ({ project }: ProjectCardProps) => {
  const navigate = useNavigate();
  const { t } = useLanguage();

  // TODO: Add image/thumbnail support for project cards when backend supports it.

  const handleCardClick = () => {
    navigate(`/projects/${project.id}`);
  };

  const stopPropagation = (e: MouseEvent) => {
    e.stopPropagation();
  };

  // Truncate members list
  const memberNames = project.members.map(m => m.name.split(' ')[0]);
  const displayedMembers = memberNames.slice(0, 3).join(', ') + (memberNames.length > 3 ? '...' : '');

  return (
    <div 
      onClick={handleCardClick}
      className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer overflow-hidden border border-slate-100 flex flex-col h-full"
    >
      {/* Header Area */}
      <div className="p-4 flex justify-between items-start gap-2">
        <button
          onClick={(e) => { e.stopPropagation(); navigate(`/courses/${project.course.id}`); }}
          className="px-2 py-1 bg-tul-blue/10 text-tul-blue text-xs font-bold rounded uppercase tracking-wider hover:bg-tul-blue/20 transition-colors"
        >
          {project.course.code}
        </button>
        <span className="px-2 py-1 bg-slate-100 text-slate-500 text-xs font-medium rounded">
          {project.academic_year}/{project.academic_year + 1}
        </span>
      </div>

      {/* Content */}
      <div className="px-4 pb-4 flex-grow">
        <h3 className="text-lg font-bold text-slate-800 mb-2 group-hover:text-tul-blue transition-colors">
          {project.title}
        </h3>
        <p className="text-slate-600 text-sm line-clamp-3 mb-4">
          {project.description || t('project.no_description')}
        </p>

        {/* Technologies */}
        <div className="flex flex-wrap gap-1 mb-4">
          <Tag size={14} className="text-slate-400 mr-1" />
          {project.technologies.slice(0, 5).map((tech, idx) => (
            <span 
              key={idx} 
              className="px-2 py-0.5 bg-slate-50 text-slate-500 text-[10px] font-semibold rounded-full border border-slate-100 uppercase"
            >
              {tech}
            </span>
          ))}
          {project.technologies.length > 5 && (
            <span className="text-[10px] font-semibold text-slate-400 self-center">
              +{project.technologies.length - 5}
            </span>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-slate-50 border-t border-slate-100 flex justify-between items-center mt-auto">
        <div className="flex items-center gap-2 text-slate-500 text-xs font-medium">
          <Users size={14} />
          <span>{displayedMembers}</span>
        </div>
        
        <div className="flex items-center gap-3">
          {project.github_url && (
            <a 
              href={project.github_url} 
              target="_blank" 
              rel="noopener noreferrer"
              onClick={stopPropagation}
              className="text-slate-400 hover:text-slate-800 transition-colors"
              title={t('project.source_code')}
            >
              <Code size={18} />
            </a>
          )}
          {project.live_url && (
            <a 
              href={project.live_url} 
              target="_blank" 
              rel="noopener noreferrer"
              onClick={stopPropagation}
              className="text-slate-400 hover:text-tul-blue transition-colors"
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
