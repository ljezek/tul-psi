import { useState, useEffect, FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { 
  Calendar, 
  ClipboardCheck, 
  Globe,
  Users,
  Plus
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { getProjects, addProjectMember, ApiError } from '@/api';
import { ProjectPublic } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { GitHubLogo } from '@/components/icons/GitHubLogo';
import { CourseEvaluationStatusCard } from '@/components/student/CourseEvaluationStatusCard';

import { ProjectCard } from '@/components/project/ProjectCard';

export const StudentHome = () => {
  // ... rest of state ...
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <header className="mb-12">
        <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2">
          {t('student.zone_title')}
        </h1>
        <div className="flex items-center gap-2 text-slate-500 font-medium">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          {t('student.logged_as')}: <span className="text-tul-blue font-bold">{user?.name}</span>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {projects.map(project => (
          <ProjectCard 
            key={project.id} 
            project={project} 
            href={`/projects/${project.id}`}
          >
            {/* Add Member (Student) */}
            {!project.results_unlocked && (
              <div className="mb-6">
                {addingMemberTo === project.id ? (
                  <form onSubmit={(e) => handleAddMember(e, project.id)} className="flex items-center gap-2 mt-4 bg-slate-50 p-2 rounded-xl border border-slate-100">
                    <div className="relative flex-1">
                      <input 
                        type="text" 
                        required 
                        placeholder={t('form.email_placeholder')}
                        value={memberEmail}
                        onChange={e => setMemberEmail(e.target.value.split('@')[0])}
                        className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 pr-16 text-sm text-slate-900 focus:outline-none focus:border-tul-blue focus:ring-1"
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-[10px] pointer-events-none">@tul.cz</span>
                    </div>
                    <button type="submit" className="text-xs bg-slate-700 hover:bg-slate-800 text-white px-3 py-1.5 rounded-lg font-bold transition-colors">
                      {t('form.add')}
                    </button>
                    <button type="button" onClick={() => setAddingMemberTo(null)} className="text-xs text-slate-500 hover:text-slate-700 font-bold">
                      {t('lecturer.cancel')}
                    </button>
                  </form>
                ) : (
                  <button 
                    onClick={() => setAddingMemberTo(project.id)}
                    className="text-[10px] font-bold text-tul-blue hover:text-tul-blue/80 transition-colors uppercase tracking-wider flex items-center group/add"
                  >
                    <Plus size={12} className="mr-1 group-hover/add:scale-110 transition-transform"/> {t('lecturer.add_member')}
                  </button>
                )}
              </div>
            )}

            <CourseEvaluationStatusCard 
              project={project}
              user={user}
              className="pt-6 border-t border-slate-50"
            />
          </ProjectCard>
        ))}
      </div>
    </div>
  );
};
