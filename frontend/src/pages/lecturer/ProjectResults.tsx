import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Award, 
  CheckCircle, 
  XCircle, 
  Users, 
  ListChecks,
  Mail,
  Globe,
  ExternalLink
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useLanguage } from '@/contexts/LanguageContext';
import { getProject } from '@/api';
import { ProjectPublic } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { GitHubLogo } from '@/components/icons/GitHubLogo';

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

  const getScoreColor = (score: number, max: number) => {
    const ratio = score / max;
    if (ratio < 0.5) return 'text-red-500';
    if (ratio < 0.75) return 'text-amber-500';
    return 'text-green-500';
  };

  if (loading) return <div className="py-20"><LoadingSpinner /></div>;
  if (error || !project || !stats) return <div className="max-w-7xl mx-auto px-4 py-12"><ErrorMessage message={error || t('projectDetail.not_found')} onRetry={fetchData} retryLabel={t('error.retry')} /></div>;

  const totalPossible = project.course.evaluation_criteria.reduce((s, c) => s + c.max_score, 0);
  const passRatio = stats.totalLecturerAvg / totalPossible;
  const passColorClass = passRatio < 0.5 ? 'text-red-600' : passRatio < 0.75 ? 'text-amber-600' : 'text-green-600';

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
          <div className="space-y-6 flex-1">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <span className="bg-tul-blue text-white px-3 py-1 rounded text-[10px] font-black uppercase tracking-widest">
                  {project.course.code}
                </span>
                <span className="bg-slate-50 px-3 py-1 rounded border border-slate-100 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                  {project.academic_year}
                </span>
              </div>
              <h1 className="text-3xl font-black text-slate-900 leading-tight mb-4">
                {project.title}
              </h1>
              
              <div className="flex flex-wrap gap-4 text-sm font-bold">
                {project.github_url && (
                  <>
                    <a href={project.github_url} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 text-slate-500 hover:text-tul-blue transition-colors">
                      <GitHubLogo size={14} /> {t('common.repo')}
                    </a>
                    <a href={`${project.github_url}/graphs/contributors`} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 text-slate-500 hover:text-tul-blue transition-colors">
                      <Users size={14} /> {t('project.contributors')}
                    </a>
                  </>
                )}
                {project.live_url && (
                  <a href={project.live_url} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 text-slate-500 hover:text-tul-blue transition-colors">
                    <Globe size={14} /> {t('common.app')}
                  </a>
                )}
                <Link to={`/projects/${project.id}`} className="flex items-center gap-1.5 text-tul-blue hover:underline">
                  <ExternalLink size={14} /> {t('projectDetail.title')}
                </Link>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-6 pt-6 border-t border-slate-50">
              {project.members.map(m => (
                <div key={m.id} className="space-y-1">
                  <div className="text-xs font-black text-slate-800">{m.name}</div>
                  <div className="flex items-center gap-3">
                    <a href={`mailto:${m.email}`} title={m.email || undefined} className="text-slate-400 hover:text-tul-blue transition-colors">
                      <Mail size={12} />
                    </a>
                    {m.github_alias && (
                      <a href={`https://github.com/${m.github_alias}`} target="_blank" rel="noreferrer" title={m.github_alias} className="text-slate-400 hover:text-tul-blue transition-colors">
                        <GitHubLogo size={12} />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-8 bg-slate-50/50 p-6 rounded-2xl border border-slate-100 h-fit self-center">
            <div className="text-right">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">
                {t('lecturer.lecturer_scores')}
              </span>
              <div className="flex items-baseline gap-1">
                <span className={`text-4xl font-black ${passColorClass}`}>
                  {Math.round(stats.totalLecturerAvg * 10) / 10}
                </span>
                <span className="text-slate-300 font-bold text-xl">/</span>
                <span className="text-slate-400 font-bold text-xl">{totalPossible}</span>
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
                    <span className={`font-black ${getScoreColor(c.avg, c.max_score)}`}>{Math.round(c.avg * 10) / 10} / {c.max_score}</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-1000 ${c.avg / c.max_score < 0.5 ? 'bg-red-500' : c.avg / c.max_score < 0.75 ? 'bg-amber-500' : 'bg-green-500'}`}
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
                      <div className="flex items-center gap-2">
                        <div className="text-sm font-black text-slate-800 truncate">{member.name}</div>
                        <div className="flex items-center gap-1.5">
                          <a href={`mailto:${member.email}`} title={member.email || undefined} className="text-slate-300 hover:text-tul-blue transition-colors">
                            <Mail size={10} />
                          </a>
                          {member.github_alias && (
                            <a href={`https://github.com/${member.github_alias}`} target="_blank" rel="noreferrer" title={member.github_alias} className="text-slate-300 hover:text-tul-blue transition-colors">
                              <GitHubLogo size={10} />
                            </a>
                          )}
                        </div>
                      </div>
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
          <section className="space-y-8">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-black text-slate-900 uppercase tracking-widest flex items-center gap-3">
                <Award size={24} className="text-tul-blue" />
                {t('lecturer.lecturer_scores')}
              </h2>
            </div>
            
            <div className="space-y-12">
              {project.course.evaluation_criteria.map((criterion) => (
                <div key={criterion.code} className="space-y-4">
                  <div className="flex items-center gap-4">
                    <h3 className="text-[11px] font-black text-slate-900 uppercase tracking-widest px-4 py-1.5 bg-slate-50 rounded-lg border border-slate-200 shadow-sm">
                      {criterion.description}
                    </h3>
                    <div className="h-px bg-slate-200 flex-1" />
                  </div>

                  <div className="bg-white rounded-3xl shadow-lg border border-slate-100 overflow-hidden">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="bg-slate-50/80 border-b border-slate-100">
                          <th className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-8 py-3 text-left w-[40%]">
                            {t('student.label_strengths')}
                          </th>
                          <th className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-8 py-3 text-left w-[40%]">
                            {t('student.label_improvements')}
                          </th>
                          <th className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-8 py-3 text-center w-[20%]">
                            {t('lecturer.score')}
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {project.project_evaluations?.map((ev) => {
                          const score = ev.scores.find(s => s.criterion_code === criterion.code);
                          if (!score) return null;

                          return (
                            <tr key={ev.lecturer_id} className="group hover:bg-slate-50/30 transition-colors">
                              <td className="px-8 py-6 text-sm text-slate-600 italic leading-relaxed whitespace-pre-line prose prose-sm max-w-none">
                                <ReactMarkdown>{score.strengths}</ReactMarkdown>
                              </td>
                              <td className="px-8 py-6 text-sm text-slate-600 italic leading-relaxed whitespace-pre-line prose prose-sm max-w-none border-l border-slate-50">
                                <ReactMarkdown>{score.improvements}</ReactMarkdown>
                              </td>
                              <td className="px-8 py-6 text-center border-l border-slate-50">
                                <span className={`px-4 py-1.5 rounded-xl text-sm font-black bg-white border border-slate-200 shadow-sm ${getScoreColor(score.score, criterion.max_score)}`}>
                                  {score.score}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
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
              <div className="space-y-12">
                {project.members.map((member) => {
                  const receivedFeedback = stats.peerFeedback.filter(f => f.receiving_student_id === member.id);
                  if (receivedFeedback.length === 0) return null;

                  return (
                    <div key={member.id} className="space-y-4">
                      <div className="flex items-center gap-4">
                        <h3 className="text-[11px] font-black text-purple-600 uppercase tracking-widest px-4 py-1.5 bg-purple-50 rounded-lg border border-purple-200 shadow-sm flex items-center gap-2">
                          <Users size={14} />
                          {member.name}
                        </h3>
                        <div className="h-px bg-purple-100 flex-1" />
                      </div>

                      <div className="bg-white rounded-3xl shadow-lg border border-slate-100 overflow-hidden">
                        <table className="w-full border-collapse">
                          <thead>
                            <tr className="bg-slate-50/80 border-b border-slate-100">
                              <th className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-8 py-3 text-left w-[40%]">
                                {t('student.label_strengths')}
                              </th>
                              <th className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-8 py-3 text-left w-[40%]">
                                {t('student.label_improvements')}
                              </th>
                              <th className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-8 py-3 text-center w-[20%]">
                                {t('lecturer.score')}
                              </th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-50">
                            {receivedFeedback.map((f, i) => (
                              <tr key={i} className="group hover:bg-slate-50/30 transition-colors">
                                <td className="px-8 py-6 text-sm text-slate-600 italic leading-relaxed whitespace-pre-line prose prose-sm max-w-none">
                                  <ReactMarkdown>{f.strengths || '---'}</ReactMarkdown>
                                </td>
                                <td className="px-8 py-6 text-sm text-slate-600 italic leading-relaxed whitespace-pre-line prose prose-sm max-w-none border-l border-slate-50">
                                  <ReactMarkdown>{f.improvements || '---'}</ReactMarkdown>
                                </td>
                                <td className="px-8 py-6 text-center border-l border-slate-50">
                                  <span className={`px-4 py-1.5 rounded-xl text-sm font-black bg-white border border-slate-200 shadow-sm ${f.bonus_points >= 0 ? 'text-purple-600' : 'text-red-600'}`}>
                                    {f.bonus_points}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
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
