import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Award, 
  CheckCircle, 
  XCircle, 
  Users, 
  ThumbsUp, 
  TrendingUp,
  ListChecks
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useLanguage } from '@/contexts/LanguageContext';
import { getProject } from '@/api';
import { ProjectPublic } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

export const ProjectResults = () => {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const { t } = useLanguage();
  const navigate = useNavigate();

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

  const stats = useMemo(() => {
    if (!project) return null;
    
    const criteria = project.course.evaluation_criteria;
    const evaluations = project.project_evaluations || [];
    
    const criteriaAverages = criteria.map(criterion => {
      const scores = evaluations.map(e => e.scores.find(s => s.criterion_code === criterion.code)?.score || 0);
      const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
      return { ...criterion, avg };
    });

    const totalLecturerAvg = criteriaAverages.reduce((sum, c) => sum + c.avg, 0);
    const peerFeedback = project.received_peer_feedback || [];

    return {
      criteriaAverages,
      totalLecturerAvg,
      peerFeedback
    };
  }, [project]);

  if (loading) return <div className="py-20"><LoadingSpinner /></div>;
  if (error || !project || !stats) return <div className="max-w-7xl mx-auto px-4 py-12"><ErrorMessage message={error || t('projectDetail.not_found')} onRetry={fetchData} retryLabel={t('error.retry')} /></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="space-y-6">
        <button 
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2 text-sm font-bold text-slate-400 hover:text-tul-blue transition-colors group"
        >
          <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
          {t('common.back')}
        </button>
        
        <div className="bg-white p-8 rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 flex flex-col md:flex-row justify-between gap-8">
          <div className="space-y-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="bg-tul-blue text-white px-3 py-1 rounded text-[10px] font-black uppercase tracking-widest">
                  {project.course.code}
                </span>
                <span className="bg-slate-50 px-3 py-1 rounded border border-slate-100 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                  {project.academic_year}
                </span>
              </div>
              <h1 className="text-3xl font-black text-slate-900 leading-tight">
                {project.title}
              </h1>
            </div>
            
            <div className="flex flex-wrap gap-4">
              {project.members.map(m => (
                <div key={m.id} className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-100">
                  <div className="w-5 h-5 rounded-full bg-white border border-slate-200 flex items-center justify-center">
                    <Users size={10} className="text-slate-400" />
                  </div>
                  <span className="text-xs font-bold text-slate-600">{m.name || m.email}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-8 bg-slate-50/50 p-6 rounded-2xl border border-slate-100 h-fit">
            <div className="text-right">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">
                {t('lecturer.lecturer_scores')}
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-black text-tul-blue">
                  {Math.round(stats.totalLecturerAvg * 10) / 10}
                </span>
                <span className="text-slate-300 font-bold text-xl">/</span>
                <span className="text-slate-400 font-bold text-xl">{project.course.evaluation_criteria.reduce((s, c) => s + c.max_score, 0)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Summary and Student results */}
        <div className="lg:col-span-1 space-y-8">
          {/* Criterion Summary */}
          <section className="bg-white rounded-3xl shadow-lg border border-slate-100 overflow-hidden">
            <div className="bg-slate-50 px-6 py-4 border-b border-slate-100">
              <h3 className="text-xs font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
                <ListChecks size={14} className="text-tul-blue" />
                {t('lecturer.avg_score')}
              </h3>
            </div>
            <div className="p-6 space-y-4">
              {stats.criteriaAverages.map(c => (
                <div key={c.code} className="space-y-2">
                  <div className="flex justify-between items-center text-xs font-bold">
                    <span className="text-slate-500 truncate mr-2">{c.description}</span>
                    <span className="text-slate-700">{Math.round(c.avg * 10) / 10} / {c.max_score}</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-tul-blue transition-all duration-1000"
                      style={{ width: `${(c.avg / c.max_score) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Student Final Scores */}
          <section className="bg-white rounded-3xl shadow-lg border border-slate-100 overflow-hidden">
            <div className="bg-slate-50 px-6 py-4 border-b border-slate-100">
              <h3 className="text-xs font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
                <Users size={14} className="text-tul-blue" />
                {t('student.results_status')}
              </h3>
            </div>
            <div className="p-6 space-y-4">
              {project.members.map(member => {
                const receivedFeedback = stats.peerFeedback.filter(f => f.receiving_student_id === member.id);
                const memberBonus = receivedFeedback.length > 0 
                    ? receivedFeedback.reduce((sum, f) => sum + f.bonus_points, 0) / receivedFeedback.length
                    : 0;
                
                const totalPoints = stats.totalLecturerAvg + memberBonus;
                const isPass = totalPoints >= project.course.min_score;

                return (
                  <div key={member.id} className="p-4 rounded-2xl border border-slate-100 flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <div className="text-sm font-black text-slate-800 truncate">{member.name || member.email}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] font-bold text-purple-500">Peer: +{Math.round(memberBonus * 10) / 10}</span>
                        <span className="text-[10px] font-bold text-slate-300">&bull;</span>
                        <span className="text-[10px] font-black text-slate-500">{t('results.total_score')}: {Math.round(totalPoints * 10) / 10}</span>
                      </div>
                    </div>
                    <div className={`shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-lg text-[9px] font-black uppercase tracking-wider ${isPass ? 'bg-green-50 text-green-600 border border-green-100' : 'bg-red-50 text-red-600 border border-red-100'}`}>
                      {isPass ? <CheckCircle size={10} /> : <XCircle size={10} />}
                      {isPass ? t('results.pass') : t('results.fail')}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </div>

        {/* Middle and Right Column: Detailed Feedback */}
        <div className="lg:col-span-2 space-y-12">
          {/* Lecturer Feedback */}
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-black text-slate-900 uppercase tracking-widest flex items-center gap-3">
                <Award size={24} className="text-tul-blue" />
                {t('lecturer.lecturer_scores')}
              </h2>
            </div>
            <div className="grid grid-cols-1 gap-6">
              {project.project_evaluations?.map((ev) => (
                <div key={ev.lecturer_id} className="bg-white rounded-3xl shadow-lg border border-slate-100 overflow-hidden">
                  <div className="px-8 py-4 bg-slate-50 border-b border-slate-100 flex justify-between items-center">
                    <span className="text-sm font-black text-slate-800 uppercase tracking-wide flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-tul-blue" />
                      {/* TODO: We need lecturer name in ProjectEvaluationDetail or fetch from somewhere */}
                      {t('results.feedback')} #{ev.lecturer_id}
                    </span>
                    <span className="bg-tul-blue/10 text-tul-blue px-3 py-1 rounded-lg text-xs font-black">
                      {ev.scores.reduce((sum, s) => sum + s.score, 0)} {t('label.points')}
                    </span>
                  </div>
                  <div className="p-8 space-y-8">
                    {ev.scores.map((s) => {
                      const criterion = project.course.evaluation_criteria.find(c => c.code === s.criterion_code);
                      return (
                        <div key={s.criterion_code} className="space-y-4">
                          <div className="flex justify-between items-center">
                            <h4 className="text-xs font-black text-slate-500 uppercase tracking-widest">{criterion?.description || s.criterion_code}</h4>
                            <span className="text-sm font-black text-slate-900">{s.score} / {criterion?.max_score}</span>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                              <div className="text-[10px] font-black text-green-600 uppercase tracking-widest flex items-center gap-1">
                                <ThumbsUp size={12} />
                                {t('student.label_strengths')}
                              </div>
                              <div className="bg-green-50/30 p-4 rounded-2xl border border-green-100/50 text-sm text-slate-600 italic leading-relaxed whitespace-pre-line prose prose-sm max-w-none">
                                <ReactMarkdown>{s.strengths}</ReactMarkdown>
                              </div>
                            </div>
                            <div className="space-y-2">
                              <div className="text-[10px] font-black text-amber-600 uppercase tracking-widest flex items-center gap-1">
                                <TrendingUp size={12} />
                                {t('student.label_improvements')}
                              </div>
                              <div className="bg-amber-50/30 p-4 rounded-2xl border border-amber-100/50 text-sm text-slate-600 italic leading-relaxed whitespace-pre-line prose prose-sm max-w-none">
                                <ReactMarkdown>{s.improvements}</ReactMarkdown>
                              </div>
                            </div>
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
            <section className="space-y-6">
              <h2 className="text-xl font-black text-slate-900 uppercase tracking-widest flex items-center gap-3">
                <Users size={24} className="text-purple-600" />
                {t('lecturer.peer_feedback')}
              </h2>
              <div className="space-y-10">
                {project.members.map((member) => {
                  const receivedFeedback = stats.peerFeedback.filter(f => f.receiving_student_id === member.id);
                  if (receivedFeedback.length === 0) return null;

                  return (
                    <div key={member.id} className="space-y-4">
                      <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-2">
                        <Users size={16} />
                        {member.name || member.email}
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {receivedFeedback.map((f, i) => (
                          <div key={i} className="bg-white rounded-3xl shadow-md border border-slate-100 overflow-hidden flex flex-col">
                            <div className="px-6 py-3 bg-purple-50/50 border-b border-purple-100 flex justify-between items-center">
                              <span className="text-[10px] font-black text-purple-400 uppercase tracking-widest">{t('results.feedback')} #{i + 1}</span>
                              <span className={`text-xs font-black ${f.bonus_points >= 0 ? 'text-purple-600' : 'text-red-600'}`}>
                                {f.bonus_points >= 0 ? '+' : ''}{f.bonus_points} {t('label.points')}
                              </span>
                            </div>
                            <div className="p-6 space-y-4 flex-grow">
                              <div className="space-y-2">
                                <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{t('student.label_strengths')}</div>
                                <div className="text-xs text-slate-600 italic leading-relaxed whitespace-pre-line prose prose-sm max-w-none">
                                  <ReactMarkdown>{f.strengths || '---'}</ReactMarkdown>
                                </div>
                              </div>
                              <div className="space-y-2">
                                <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{t('student.label_improvements')}</div>
                                <div className="text-xs text-slate-600 italic leading-relaxed whitespace-pre-line prose prose-sm max-w-none">
                                  <ReactMarkdown>{f.improvements || '---'}</ReactMarkdown>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
};
