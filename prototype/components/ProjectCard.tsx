import React from 'react';
import { Project, Subject, Student } from '../types';
import { Github, ExternalLink, Users, Calendar, Tag } from 'lucide-react';

interface ProjectCardProps {
  project: Project;
  subject?: Subject;
  authors: Student[];
  onClick: () => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({ project, subject, authors, onClick }) => {
  return (
    <div 
      className="group bg-white rounded-xl overflow-hidden border border-slate-200 shadow-sm hover:shadow-xl hover:border-blue-200 transition-all duration-300 flex flex-col h-full cursor-pointer"
      onClick={onClick}
    >
      <div className="relative h-48 overflow-hidden bg-slate-100">
        <img 
          src={project.imageUrl} 
          alt={project.title} 
          className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
        />
        <div className="absolute top-2 right-2 bg-white/90 backdrop-blur-sm px-2 py-1 rounded text-xs font-semibold text-slate-700 shadow-sm">
          {project.academicYear}
        </div>
      </div>

      <div className="p-5 flex flex-col flex-grow">
        <div className="mb-2 flex items-center gap-2 text-xs font-medium text-tul-blue">
          <span className="bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
            {subject?.code || 'N/A'}
          </span>
        </div>

        <h3 className="text-lg font-bold text-slate-900 mb-2 group-hover:text-tul-blue transition-colors">
          {project.title}
        </h3>

        <p className="text-slate-600 text-sm mb-4 line-clamp-3 flex-grow">
          {project.description}
        </p>

        <div className="flex flex-wrap gap-1 mb-4">
          {project.tags.map(tag => (
            <span key={tag} className="text-[10px] bg-slate-100 text-slate-600 px-2 py-1 rounded-full flex items-center gap-1">
              <Tag size={10} /> {tag}
            </span>
          ))}
        </div>

        <div className="border-t border-slate-100 pt-4 mt-auto flex justify-between items-center">
          <div className="flex items-center gap-1 text-slate-500 text-xs">
            <Users size={14} />
            <span className="truncate max-w-[120px]">
              {authors.map(a => a.name.split(' ')[1]).join(', ')}
            </span>
          </div>
          
          <div className="flex gap-2" onClick={e => e.stopPropagation()}>
            {project.githubUrl && (
              <a href={project.githubUrl} target="_blank" rel="noreferrer" className="text-slate-400 hover:text-slate-800 transition-colors">
                <Github size={18} />
              </a>
            )}
            {project.liveUrl && (
              <a href={project.liveUrl} target="_blank" rel="noreferrer" className="text-slate-400 hover:text-tul-blue transition-colors">
                <ExternalLink size={18} />
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};