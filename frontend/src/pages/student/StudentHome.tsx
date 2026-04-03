import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Calendar, CheckCircle, Clock, ExternalLink, ClipboardCheck } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { getProjects } from '@/api';
import { ProjectPublic } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Button } from '@/components/ui/Button';

export const StudentHome = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [projects, setProjects] = useState<ProjectPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMyProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const allProjects = await getProjects();
      // Filter projects where current user is a member
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
      fetchMyProjects();
    }
  }, [user]);

  if (loading) return <div className="py-20"><LoadingSpinner /></div>;
  if (error) return <div className="max-w-7xl mx-auto px-4 py-12"><ErrorMessage message={error} onRetry={fetchMyProjects} retryLabel={t('error.retry')} /></div>;

  if (projects.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 p-12 max-w-lg mx-auto">
          <div className="bg-slate-50 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 text-slate-400">
            <BookOpen size={40} />
          </div>
          <h2 className="text-2xl font-black text-slate-800 mb-2">{t('student.no_project')}</h2>
          <p className="text-slate-500 mb-8">{t('student.contact_teacher')}</p>
          <Link to="/">
            <Button variant="outline" className="rounded-xl">{t('project.back_to_projects')}</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-10">
        <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2">
          {t('student.zone_title')}
        </h1>
        <p className="text-slate-500 font-medium text-lg">
          {t('student.logged_as')}: <span className="text-tul-blue font-bold">{user?.name}</span>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {projects.map(project => {
          // Check evaluation status
          const myEval = (project.course_evaluations || []).find(e => e.student_id === user?.id);
          const isSubmitted = myEval?.submitted === true;
          const isDraft = myEval && !myEval.submitted;

          return (
            <div key={project.id} className="group bg-white rounded-3xl border border-slate-200/60 shadow-sm hover:shadow-xl hover:shadow-slate-200/50 hover:border-tul-blue/30 transition-all duration-300 overflow-hidden flex flex-col">
              <div className="p-8 flex-grow">
                <div className="flex justify-between items-start mb-4">
                  <div className="bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-100 text-[10px] font-black uppercase tracking-widest text-slate-500">
                    {project.course.code}
                  </div>
                  <div className="flex items-center gap-1.5 text-xs font-bold text-slate-400">
                    <Calendar size={14} />
                    {project.academic_year}
                  </div>
                </div>

                <h3 className="text-xl font-black text-slate-800 mb-6 group-hover:text-tul-blue transition-colors line-clamp-2 min-h-[3.5rem]">
                  {project.title}
                </h3>

                <div className="space-y-4 pt-4 border-t border-slate-50">
                  {/* Evaluation Status */}
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      {t('student.evaluation_status')}
                    </span>
                    {isSubmitted ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-green-50 text-green-700 text-[10px] font-black uppercase border border-green-100">
                        <CheckCircle size={12} />
                        {t('student.submitted')}
                      </span>
                    ) : isDraft ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-50 text-amber-700 text-[10px] font-black uppercase border border-amber-100">
                        <Clock size={12} />
                        {t('student.draft')}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-500 text-[10px] font-black uppercase border border-slate-200">
                        <Clock size={12} />
                        {t('student.not_started')}
                      </span>
                    )}
                  </div>

                  {/* Results Status */}
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      {t('student.results_status')}
                    </span>
                    {project.results_unlocked ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-green-50 text-green-700 text-[10px] font-black uppercase border border-green-100">
                        <CheckCircle size={12} />
                        {t('student.results_available')}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 text-slate-400 text-[10px] font-black uppercase border border-slate-100">
                        <Clock size={12} />
                        {t('student.results_pending')}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="p-6 bg-slate-50/50 border-t border-slate-100 grid grid-cols-2 gap-4">
                {!isSubmitted ? (
                  <Link to={`/student/project/${project.id}/evaluate`} className="col-span-2">
                    <Button className="w-full rounded-xl font-bold gap-2">
                      <ClipboardCheck size={18} />
                      {t('student.submit_evaluation')}
                    </Button>
                  </Link>
                ) : (
                  <Button disabled className="w-full rounded-xl font-bold gap-2 opacity-50 grayscale cursor-not-allowed">
                    <CheckCircle size={18} />
                    {t('student.submitted')}
                  </Button>
                )}

                <Link
                  to={`/projects/${project.id}`}
                  className={isSubmitted ? 'col-span-1' : (project.results_unlocked ? 'col-span-1' : 'col-span-2')}
                >
                  <Button variant="outline" className="w-full rounded-xl font-bold gap-2 bg-white">
                    <ExternalLink size={18} />
                    {t('projectDetail.title')}
                  </Button>
                </Link>

                {project.results_unlocked && (
                  <Link
                    to={`/student/project/${project.id}/results`}
                    className={isSubmitted ? 'col-span-2' : 'col-span-1'}
                  >
                    <Button variant="outline" className="w-full rounded-xl font-bold gap-2 border-tul-blue text-tul-blue bg-white hover:bg-tul-blue/5">
                      {t('student.view_results')}
                    </Button>
                  </Link>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
