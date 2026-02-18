import React from 'react';
import { Project, Subject, Student } from '../types';
import { X, Github, ExternalLink, Calendar, Users, BookOpen } from 'lucide-react';
import { Button } from './Button';
import { useLanguage } from '../LanguageContext';

interface ProjectModalProps {
  project: Project | null;
  subject?: Subject;
  authors: Student[];
  isOpen: boolean;
  onClose: () => void;
}

export const ProjectModal: React.FC<ProjectModalProps> = ({ project, subject, authors, isOpen, onClose }) => {
  const { t } = useLanguage();
  if (!isOpen || !project) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div className="relative bg-white rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col md:flex-row">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 p-2 bg-white/50 hover:bg-slate-100 rounded-full z-10 transition-colors"
        >
          <X size={20} className="text-slate-600" />
        </button>

        {/* Image Side */}
        <div className="w-full md:w-1/3 bg-slate-100 min-h-[200px] md:min-h-full">
          <img 
            src={project.imageUrl} 
            alt={project.title} 
            className="w-full h-full object-cover"
          />
        </div>

        {/* Info Side */}
        <div className="w-full md:w-2/3 p-6 md:p-8 flex flex-col">
          <div className="flex items-center gap-2 mb-4">
             <span className="px-2 py-1 bg-blue-100 text-tul-blue text-xs font-bold rounded uppercase tracking-wider">
               {subject?.code}
             </span>
             <span className="text-slate-400 text-sm flex items-center gap-1">
               <Calendar size={14} /> {project.academicYear}
             </span>
          </div>

          <h2 className="text-2xl font-bold text-slate-900 mb-4">{project.title}</h2>
          
          <div className="prose prose-slate prose-sm mb-6 text-slate-600">
            <p>{project.fullDescription}</p>
          </div>

          <div className="mt-auto space-y-6">
            <div>
              <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wide mb-2 flex items-center gap-2">
                <Users size={16} /> {t('project.team')}
              </h4>
              <ul className="space-y-1">
                {authors.map(author => (
                  <li key={author.id} className="text-sm text-slate-600 border-b border-slate-100 last:border-0 pb-1 last:pb-0">
                    {author.name} <span className="text-slate-400 text-xs">({author.email})</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex flex-wrap gap-2">
               {project.tags.map(tag => (
                 <span key={tag} className="px-3 py-1 bg-slate-100 text-slate-600 text-xs rounded-full border border-slate-200">
                   #{tag}
                 </span>
               ))}
            </div>

            <div className="flex gap-3 pt-4 border-t border-slate-100">
              {project.githubUrl && (
                <a href={project.githubUrl} target="_blank" rel="noreferrer" className="flex-1">
                  <Button variant="outline" className="w-full gap-2">
                    <Github size={18} /> {t('project.source_code')}
                  </Button>
                </a>
              )}
              {project.liveUrl && (
                <a href={project.liveUrl} target="_blank" rel="noreferrer" className="flex-1">
                  <Button variant="primary" className="w-full gap-2">
                    <ExternalLink size={18} /> {t('project.live_demo')}
                  </Button>
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};