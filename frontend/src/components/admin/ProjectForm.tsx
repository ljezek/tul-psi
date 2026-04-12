import { useState, FormEvent } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { ProjectPublic, ProjectUpdate } from '@/types';
import { Button } from '@/components/ui/Button';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

export interface ProjectFormProps {
  initialData: ProjectPublic;
  onSubmit: (data: ProjectUpdate) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export const ProjectForm = ({ initialData, onSubmit, isLoading, error }: ProjectFormProps) => {
  const { t } = useLanguage();

  const [title, setTitle] = useState(initialData.title || '');
  const [description, setDescription] = useState(initialData.description || '');
  const [githubUrl, setGithubUrl] = useState(initialData.github_url || '');
  const [liveUrl, setLiveUrl] = useState(initialData.live_url || '');
  const [technologies, setTechnologies] = useState(initialData.technologies.join(', ') || '');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    
    const data: ProjectUpdate = {
      title: title || null,
      description: description || null,
      github_url: githubUrl || null,
      live_url: liveUrl || null,
      technologies: technologies.split(',').map(t => t.trim()).filter(t => t !== ''),
    };
    
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <div>
          <label htmlFor="project-title" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('project.title')}</label>
          <input
            id="project-title"
            type="text"
            required
            value={title}
            onChange={e => setTitle(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
          />
        </div>

        <div>
          <label htmlFor="project-description" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">
            {t('project.description')}
            <span className="ml-2 lowercase font-normal opacity-60">({t('form.markdown_supported')})</span>
          </label>
          <textarea
            id="project-description"
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={5}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold text-sm"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="project-github" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('project.github_url')}</label>
            <input
              id="project-github"
              type="url"
              value={githubUrl}
              onChange={e => setGithubUrl(e.target.value)}
              placeholder="https://github.com/..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
            />
          </div>
          <div>
            <label htmlFor="project-live" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">{t('project.live_url')}</label>
            <input
              id="project-live"
              type="url"
              value={liveUrl}
              onChange={e => setLiveUrl(e.target.value)}
              placeholder="https://..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
            />
          </div>
        </div>

        <div>
          <label htmlFor="project-tech" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">
            {t('project.technologies')}
            <span className="ml-2 lowercase font-normal opacity-60">({t('project.technologies_hint')})</span>
          </label>
          <input
            id="project-tech"
            type="text"
            value={technologies}
            onChange={e => setTechnologies(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-tul-blue/20 font-bold"
          />
        </div>
      </div>

      {error && <ErrorMessage message={error} />}
      
      <div className="flex justify-end gap-3 pt-6 border-t border-slate-100">
        <Button variant="ghost" type="button" onClick={() => window.history.back()}>{t('common.cancel')}</Button>
        <Button type="submit" isLoading={isLoading} className="px-12">
          {t('common.save')}
        </Button>
      </div>
    </form>
  );
};
