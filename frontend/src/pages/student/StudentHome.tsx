import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Calendar, 
  ClipboardCheck, 
  Globe,
  Users
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { getProjects } from '@/api';
import { ProjectPublic } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { GitHubLogo } from '@/components/icons/GitHubLogo';
import { CourseEvaluationStatusCard } from '@/components/student/CourseEvaluationStatusCard';

export const StudentHome = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [projects, setProjects] = useState<ProjectPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const allProjects = await getProjects();
      // Filter projects where user is a member
      const myProjects = allProjects.filter(p => 
        p.members.some(m => m.id === user?.id)
      );
      setProjects(myProjects);
    } catch (err) {
      setError(t('dashboard.error_fetching'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchData();
    }
  }, [user]);

  if (loading) return <div className="py-20"><LoadingSpinner /></div>;
  if (error) return <div className="max-w-7xl mx-auto px-4 py-12"><ErrorMessage message={error} onRetry={fetchData} retryLabel={t('error.retry')} /></div>;

  if (projects.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="bg-white rounded-3xl p-12 shadow-xl shadow-slate-200/50 border border-slate-100">
          <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <ClipboardCheck size={40} className="text-slate-300" />
          </div>
          <h2 className="text-2xl font-black text-slate-800 mb-2">{t('student.no_project')}</h2>
          <p className="text-slate-500 font-medium">
            {t('student.contact_teacher')}
          </p>
        </div>
      </div>
    );
  }

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
        {projects.map(project => {
          return (
            <div key={project.id} className="group bg-white rounded-3xl border border-slate-200/60 shadow-sm hover:shadow-xl hover:shadow-slate-200/50 hover:border-tul-blue/30 transition-all duration-300 overflow-hidden flex flex-col">
              <div className="p-8 flex-grow">
                <div className="flex justify-between items-start mb-4">
                  <Link 
                    to={`/courses/${project.course.id}`}
                    className="bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-100 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-tul-blue hover:border-tul-blue/30 transition-colors"
                  >
                    {project.course.code}
                  </Link>
                  <div className="flex items-center gap-1.5 text-xs font-bold text-slate-400">
                    <Calendar size={14} />
                    {project.academic_year}
                  </div>
                </div>

                <Link to={`/projects/${project.id}`} className="block group/title">
                  <h3 className="text-2xl font-black text-slate-800 mb-2 group-hover/title:text-tul-blue transition-colors line-clamp-2">
                    {project.title}
                  </h3>
                </Link>

                {/* Team Members */}
                <div className="flex items-center gap-2 mb-6">
                  <Users size={14} className="text-slate-400" />
                  <div className="text-xs font-bold text-slate-500 flex flex-wrap gap-x-2">
                    {project.members.map((m, idx) => (
                      <span key={m.id} className={m.id === user?.id ? 'text-tul-blue' : ''}>
                        {m.name}{idx < project.members.length - 1 ? ',' : ''}
                      </span>
                    ))}
                  </div>
                </div>

                {/* External Links */}
                <div className="flex gap-4 mb-8">
                  {project.github_url && (
                    <a 
                      href={project.github_url} 
                      target="_blank" 
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs font-black text-slate-400 hover:text-slate-900 transition-colors uppercase tracking-wider"
                    >
                      <GitHubLogo size={14} />
                      Repo
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
                      App
                    </a>
                  )}
                </div>

                <CourseEvaluationStatusCard 
                  project={project}
                  user={user}
                  className="pt-6 border-t border-slate-50"
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
