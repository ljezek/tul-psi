import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Award, 
  CheckCircle, 
  XCircle, 
  User, 
  ThumbsUp, 
  TrendingUp,
  ShieldAlert
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useLanguage } from '@/contexts/LanguageContext';
import { getProject } from '@/api';
import { ProjectPublic } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

export const Results = () => {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const { t } = useLanguage();

  const [project, setProject] = useState<ProjectPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProject(projectId);
      setProject(data);
    } catch (err) {
      setError(t('projectDetail.error_fetching'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [projectId]);

  if (loading) return <div className="py-20"><LoadingSpinner /></div>;
  if (error || !project) return <div className="max-w-7xl mx-auto px-4 py-12"><ErrorMessage message={error || t('projectDetail.not_found')} onRetry={fetchData} retryLabel={t('error.retry')} /></div>;

  if (!project.results_unlocked) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 p-12 max-w-lg mx-auto">
          <div className="bg-amber-50 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 text-amber-500">
            <ShieldAlert size={40} />
          </div>
          <h2 className="text-2xl font-black text-slate-800 mb-2">{t('results.not_available')}</h2>
          <Link to="/student" className="mt-8 block">
            <ArrowLeft size={16} className="inline mr-2" />
            {t('project.back_to_projects')}
          </Link>
        </div>
      </div>
    );
  }

  // Calculate scores
  const criteria = project.course.evaluation_criteria;
  const evaluations = project.project_evaluations || [];
  
  const avgScores = criteria.map(criterion => {
    const scores = evaluations.map(e => e.scores.find(s => s.criterion_code === criterion.code)?.score || 0);
    const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
    return { ...criterion, avg };
  });

  const lecturerTotal = avgScores.reduce((sum, c) => sum + c.avg, 0);
  
  const peerBonus = project.received_peer_feedback || [];
  const avgPeerBonus = peerBonus.length > 0 
    ? peerBonus.reduce((sum, f) => sum + f.bonus_points, 0) / peerBonus.length 
    : (project.course.peer_bonus_budget !== null ? 0 : 0);

  const finalTotal = lecturerTotal + avgPeerBonus;
  const isPass = finalTotal >= project.course.min_score;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10">
        <Link 
          to="/student"
          className="inline-flex items-center gap-2 text-sm font-bold text-slate-400 hover:text-tul-blue transition-colors mb-6 group"
        >
          <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
          {t('project.back_to_projects')}
        </Link>
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 bg-white p-8 rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-4xl font-black text-slate-900 tracking-tight">
                {t('results.title')}
              </h1>
              <div className={`px-4 py-1.5 rounded-xl border flex items-center gap-2 font-black text-sm tracking-tight ${
                isPass ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'
              }`}>
                {isPass ? <CheckCircle size={18} /> : <XCircle size={18} />}
                {isPass ? t('results.pass') : t('results.fail')}
              </div>
            </div>
            <p className="text-slate-500 font-medium text-lg">
              {project.title} <span className="text-slate-300 mx-2">|</span> <Link to={`/courses/${project.course.id}`} className="text-tul-blue hover:underline underline-offset-4">{project.course.code}</Link>
            </p>

            <div className="flex flex-wrap gap-x-8 gap-y-2 mt-4 pt-4 border-t border-slate-50">
              <div>
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">
                  {t('results.avg_score')}
                </span>
                <span className="text-lg font-black text-slate-700">
                  {Math.round(lecturerTotal * 10) / 10}
                </span>
              </div>
              {project.course.peer_bonus_budget !== null && (
                <div>
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">
                    {t('results.avg_bonus')}
                  </span>
                  <span className="text-lg font-black text-purple-600">
                    +{Math.round(avgPeerBonus * 10) / 10}
                  </span>
                </div>
              )}
              <div>
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">
                  {t('results.min_required')}
                </span>
                <span className="text-lg font-black text-slate-400">
                  {project.course.min_score}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6 bg-slate-50/50 p-6 rounded-2xl border border-slate-100">
            <div className="text-right">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">
                {t('results.total_score')}
              </span>
              <div className="flex items-baseline gap-1">
                <span className={`text-5xl font-black ${isPass ? 'text-green-600' : 'text-red-600'}`}>
                  {Math.round(finalTotal * 10) / 10}
                </span>
                <span className="text-slate-300 font-bold text-xl">/</span>
                <span className="text-slate-400 font-bold text-xl">{criteria.reduce((s, c) => s + c.max_score, 0) + (project.course.peer_bonus_budget || 0)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-12">
        {/* Lecturer Feedback */}
        <section className="bg-white rounded-3xl shadow-lg border border-slate-100 overflow-hidden">
          <div className="bg-slate-50 px-8 py-6 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Award className="text-tul-blue" size={24} />
              <h2 className="text-xl font-black text-slate-800">{t('results.lecturer_eval')}</h2>
            </div>
            <div className="bg-tul-blue/5 text-tul-blue px-4 py-2 rounded-2xl border border-tul-blue/10 text-xs font-black uppercase">
              {t('results.avg_score')}: {Math.round(lecturerTotal * 10) / 10}
            </div>
          </div>
          <div className="p-8 space-y-12">
            {avgScores.map(c => (
              <div key={c.code} className="space-y-6 pb-12 last:pb-0 border-b last:border-0 border-slate-50">
                <div className="flex justify-between items-end">
                  <div>
                    <h3 className="text-xl font-black text-slate-800">{c.description}</h3>
                  </div>
                  <div className="text-right">
                    <span className="text-3xl font-black text-slate-700">{Math.round(c.avg * 10) / 10}</span>
                    <span className="text-slate-300 font-bold mx-1 text-xl">/</span>
                    <span className="text-slate-400 font-bold text-xl">{c.max_score}</span>
                  </div>
                </div>
                {/* Progress Bar */}
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-1000 ${
                      (c.avg / c.max_score) > 0.7 ? 'bg-green-500' : (c.avg / c.max_score) > 0.4 ? 'bg-amber-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${(c.avg / c.max_score) * 100}%` }}
                  />
                </div>
                {/* Lecturer Comments */}
                <div className="space-y-4">
                  {evaluations.map((evalItem, idx) => {
                    const score = evalItem.scores.find(s => s.criterion_code === c.code);
                    if (!score?.strengths && !score?.improvements) return null;
                    return (
                      <div key={idx} className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl bg-slate-50/30 border border-slate-100">
                        <div className="space-y-3">
                          <div className="flex items-center gap-2 text-[10px] font-black text-green-700 uppercase tracking-widest mb-1">
                            <ThumbsUp size={12} />
                            {t('student.label_strengths')}
                          </div>
                          {score.strengths ? (
                            <div className="prose prose-sm prose-slate max-w-none text-slate-600 italic">
                              <ReactMarkdown>{score.strengths}</ReactMarkdown>
                            </div>
                          ) : (
                            <p className="text-sm text-slate-300 italic">---</p>
                          )}
                        </div>
                        <div className="space-y-3">
                          <div className="flex items-center gap-2 text-[10px] font-black text-orange-700 uppercase tracking-widest mb-1">
                            <TrendingUp size={12} />
                            {t('student.label_improvements')}
                          </div>
                          {score.improvements ? (
                            <div className="prose prose-sm prose-slate max-w-none text-slate-600 italic">
                              <ReactMarkdown>{score.improvements}</ReactMarkdown>
                            </div>
                          ) : (
                            <p className="text-sm text-slate-300 italic">---</p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Peer Feedback */}
        {project.course.project_type === 'TEAM' && (
          <section className="bg-white rounded-3xl shadow-lg border border-slate-100 overflow-hidden">
            <div className="bg-slate-50 px-8 py-6 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <User className="text-purple-600" size={24} />
                <h2 className="text-xl font-black text-slate-800">{t('results.peer_feedback')}</h2>
              </div>
              {project.course.peer_bonus_budget !== null && (
                <div className="bg-purple-50 text-purple-700 px-4 py-2 rounded-2xl border border-purple-100 text-xs font-black uppercase">
                  {t('results.avg_bonus')}: {Math.round(avgPeerBonus * 10) / 10}
                </div>
              )}
            </div>
            <div className="p-8 space-y-8">
              {peerBonus.length > 0 ? (
                <div className="space-y-8">
                  {peerBonus.map((f, idx) => (
                    <div key={idx} className="bg-slate-50/50 rounded-2xl p-8 border border-slate-100 space-y-6">
                      <div className="flex justify-between items-center border-b border-slate-100 pb-4 mb-2">
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{t('results.feedback')} #{idx + 1}</span>
                        {project.course.peer_bonus_budget !== null && (
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-black text-purple-400 uppercase tracking-widest">{t('student.points_allocation')}</span>
                            <span className="text-lg font-black text-purple-600">+{f.bonus_points} {t('courseDetail.points')}</span>
                          </div>
                        )}
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="space-y-3">
                          <span className="text-[10px] font-black text-green-700 uppercase tracking-wider flex items-center gap-2">
                            <ThumbsUp size={12} />
                            {t('student.label_strengths')}
                          </span>
                          {f.strengths ? (
                            <div className="prose prose-sm prose-slate max-w-none text-slate-700 leading-relaxed italic">
                              <ReactMarkdown>{f.strengths}</ReactMarkdown>
                            </div>
                          ) : (
                            <p className="text-sm text-slate-300 italic">---</p>
                          )}
                        </div>
                        <div className="space-y-3">
                          <span className="text-[10px] font-black text-orange-700 uppercase tracking-wider flex items-center gap-2">
                            <TrendingUp size={12} />
                            {t('student.label_improvements')}
                          </span>
                          {f.improvements ? (
                            <div className="prose prose-sm prose-slate max-w-none text-slate-700 leading-relaxed italic">
                              <ReactMarkdown>{f.improvements}</ReactMarkdown>
                            </div>
                          ) : (
                            <p className="text-sm text-slate-300 italic">---</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-slate-50 rounded-3xl border border-dashed border-slate-200">
                  <p className="text-slate-400 italic">{t('feedback.no_feedback')}</p>
                </div>
              )}
            </div>
          </section>
        )}
      </div>
    </div>
  );
};
