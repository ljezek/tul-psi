import { useState, useEffect, useMemo, FormEvent } from 'react';
import { useParams, useNavigate, Link, useBlocker } from 'react-router-dom';
import { 
  Star, 
  ThumbsUp, 
  TrendingUp, 
  Save, 
  Info, 
  Award,
  CheckCircle,
  AlertCircle,
  GitPullRequest,
  Mail
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { getProject, getCourseEvaluation, submitCourseEvaluation } from '@/api';
import { ProjectPublic, CourseEvaluationSubmit } from '@/types';
import { usePointRedistribution } from '@/hooks/usePointRedistribution';
import { GitHubLogo } from '@/components/icons/GitHubLogo';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { ProjectHero } from '@/components/project/ProjectHero';
import { MemberInfo } from '@/components/project/MemberInfo';

type NotificationState = { type: 'success' | 'error'; message: string } | null;

interface StarRatingProps {
  rating: number;
  onChange: (rating: number) => void;
  disabled?: boolean;
}

const StarRating = ({ rating, onChange, disabled }: StarRatingProps) => {
  const { t } = useLanguage();
  return (
    <div className="flex gap-2">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={disabled}
          aria-label={t('common.rate_star').replace('{star}', star.toString())}
          onClick={() => onChange(star)}
          className={`transition-all ${star <= rating ? 'text-amber-400 scale-110' : 'text-slate-200 hover:text-slate-300'} ${disabled ? 'cursor-default' : 'cursor-pointer hover:scale-125'}`}
        >
          <Star size={32} fill={star <= rating ? 'currentColor' : 'none'} strokeWidth={star <= rating ? 0 : 2} />
        </button>
      ))}
    </div>
  );
};

export const CourseEvaluation = () => {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useLanguage();

  const [project, setProject] = useState<ProjectPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [notification, setNotification] = useState<NotificationState>(null);
  const [isSubmitSuccess, setIsSubmitSuccess] = useState(false);

  // Auto-dismiss success notifications after 3 seconds.
  useEffect(() => {
    if (notification?.type !== 'success') return;
    const timer = setTimeout(() => setNotification(null), 3000);
    return () => clearTimeout(timer);
  }, [notification]);

  // Form State
  const [rating, setRating] = useState(0);
  const [strengths, setStrengths] = useState('');
  const [improvements, setImprovements] = useState('');
  
  // Peer state
  const [peerTexts, setPeerState] = useState<Record<number, { strengths: string, improvements: string }>>({});
  // Bonus points loaded from an existing draft; used as the initial distribution.
  const [savedPoints, setSavedPoints] = useState<Record<number, number>>({});

  // Capture baseline for "dirty" check
  const [initialData, setInitialData] = useState<{
    rating: number;
    strengths: string;
    improvements: string;
    peerTexts: Record<number, { strengths: string, improvements: string }>;
    peerPoints: Record<number, number>;
  } | null>(null);

  const teammates = project?.members.filter(m => m.id !== user?.id) || [];
  const budget = project?.course.peer_bonus_budget;
  const isResultsUnlocked = project?.results_unlocked === true;

  const teammateIds = teammates.map(m => m.id).join(',');
  const initialPoints = useMemo(() =>
    teammates.reduce((acc, m) => {
      acc[m.id] = savedPoints[m.id] ?? (budget || 0);
      return acc;
    }, {} as Record<number, number>),
    [teammateIds, budget, savedPoints]
  );

  const { values: peerPoints, handlePointChange, remainingPoints } = usePointRedistribution(
    initialPoints,
    (budget || 0) * teammates.length,
    (budget || 0) * 2
  );

  const isDirty = useMemo(() => {
    if (!initialData) return false;
    if (rating !== initialData.rating) return true;
    if (strengths !== initialData.strengths) return true;
    if (improvements !== initialData.improvements) return true;
    
    const ids = Object.keys(initialData.peerTexts).map(Number);
    for (const tid of ids) {
      if ((peerTexts[tid]?.strengths || '') !== (initialData.peerTexts[tid]?.strengths || '')) return true;
      if ((peerTexts[tid]?.improvements || '') !== (initialData.peerTexts[tid]?.improvements || '')) return true;
    }

    for (const tid of ids) {
      if (peerPoints[tid] !== initialData.peerPoints[tid]) return true;
    }

    return false;
  }, [initialData, rating, strengths, improvements, peerTexts, peerPoints]);

  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      isDirty && !isSubmitSuccess && currentLocation.pathname !== nextLocation.pathname
  );

  useEffect(() => {
    if (blocker.state === 'blocked') {
      const proceed = window.confirm(t('student.unsaved_changes'));
      if (proceed) {
        blocker.proceed();
      } else {
        blocker.reset();
      }
    }
  }, [blocker, t]);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [projData, evalData] = await Promise.all([
        getProject(projectId),
        getCourseEvaluation(projectId).catch(err => {
          if (err.status === 404) return null;
          throw err;
        })
      ]);

      setProject(projData);

      const loadedPeerTexts: Record<number, { strengths: string, improvements: string }> = {};
      const loadedPoints: Record<number, number> = {};

      if (evalData && evalData.current_evaluation) {
        setRating(evalData.current_evaluation.rating || 0);
        setStrengths(evalData.current_evaluation.strengths || '');
        setImprovements(evalData.current_evaluation.improvements || '');
        
        (evalData.authored_peer_feedback || []).forEach(pe => {
          loadedPeerTexts[pe.receiving_student_id] = {
            strengths: pe.strengths || '',
            improvements: pe.improvements || ''
          };
          loadedPoints[pe.receiving_student_id] = pe.bonus_points;
        });
        setPeerState(loadedPeerTexts);
        if (Object.keys(loadedPoints).length > 0) {
          setSavedPoints(loadedPoints);
        }
      }

      const currentTeammates = projData.members.filter(m => m.id !== user?.id) || [];
      const currentBudget = projData.course.peer_bonus_budget || 0;
      const effectivePoints = { ...loadedPoints };
      currentTeammates.forEach(m => {
        if (effectivePoints[m.id] === undefined) {
          effectivePoints[m.id] = currentBudget;
        }
      });

      setInitialData({
        rating: evalData?.current_evaluation?.rating || 0,
        strengths: evalData?.current_evaluation?.strengths || '',
        improvements: evalData?.current_evaluation?.improvements || '',
        peerTexts: loadedPeerTexts,
        peerPoints: effectivePoints
      });

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

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    setNotification(null);
    setSubmitting(true);
    try {
      const payload: CourseEvaluationSubmit = {
        submitted: true,
        rating: rating || null,
        strengths: strengths || null,
        improvements: improvements || null,
        peer_feedback: teammates.map(m => ({
          receiving_student_id: m.id,
          strengths: peerTexts[m.id]?.strengths || null,
          improvements: peerTexts[m.id]?.improvements || null,
          bonus_points: peerPoints[m.id] || 0
        }))
      };

      await submitCourseEvaluation(projectId, payload);
      setIsSubmitSuccess(true);
      setNotification({ type: 'success', message: t('student.submit_success') });
      setTimeout(() => navigate('/student'), 1500);
    } catch (err) {
      console.error(err);
      setNotification({ type: 'error', message: t('student.submit_error') });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="py-20"><LoadingSpinner /></div>;
  if (error || !project) return <div className="max-w-7xl mx-auto px-4 py-12"><ErrorMessage message={error || t('projectDetail.not_found')} onRetry={fetchData} retryLabel={t('error.retry')} /></div>;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      <ProjectHero 
        project={project}
        backLink={{ to: '/student', label: t('project.back_to_student_zone') }}
        rightContent={
          isResultsUnlocked && (
            <div className="bg-green-50 text-green-700 px-4 py-2 rounded-2xl border border-green-100 flex items-center gap-2 text-sm font-black uppercase">
              <CheckCircle size={18} />
              {t('student.results_available')}
            </div>
          )
        }
      />

      <form onSubmit={handleSubmit} className="space-y-12">
        {/* Subject Evaluation Section */}
        <section className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden">
          <div className="bg-slate-50 px-8 py-6 border-b border-slate-100 flex items-center gap-3">
            <ThumbsUp className="text-tul-blue" size={24} />
            <h2 className="text-xl font-black text-slate-800">{t('student.course_eval')}</h2>
          </div>
          <div className="p-8 space-y-8">
            <div className="space-y-4">
              <label className="block text-sm font-black text-slate-500 uppercase tracking-widest">{t('student.course_eval')}</label>
              <StarRating rating={rating} onChange={setRating} disabled={isResultsUnlocked} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-3">
                <label htmlFor="strengths" className="flex items-center gap-2 text-sm font-black text-green-700 uppercase tracking-widest">
                  <ThumbsUp size={16} /> {t('student.course_strengths')}
                </label>
                <textarea
                  id="strengths"
                  required
                  disabled={isResultsUnlocked}
                  value={strengths}
                  onChange={(e) => setStrengths(e.target.value)}
                  className="w-full h-40 p-4 rounded-2xl border border-slate-200 focus:ring-4 focus:ring-tul-blue/10 focus:border-tul-blue transition-all bg-slate-50 focus:bg-white resize-none text-slate-700 font-medium disabled:opacity-70"
                  placeholder={t('student.course_strengths_ph')}
                />
              </div>
              <div className="space-y-3">
                <label htmlFor="improvements" className="flex items-center gap-2 text-sm font-black text-orange-700 uppercase tracking-widest">
                  <TrendingUp size={16} /> {t('student.course_improvements')}
                </label>
                <textarea
                  id="improvements"
                  required
                  disabled={isResultsUnlocked}
                  value={improvements}
                  onChange={(e) => setImprovements(e.target.value)}
                  className="w-full h-40 p-4 rounded-2xl border border-slate-200 focus:ring-4 focus:ring-tul-blue/10 focus:border-tul-blue transition-all bg-slate-50 focus:bg-white resize-none text-slate-700 font-medium disabled:opacity-70"
                  placeholder={t('student.course_improvements_ph')}
                />
              </div>
            </div>
          </div>
        </section>

        {/* Peer Evaluation Section */}
        {teammates.length > 0 && (
          <section className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden">
            <div className="bg-slate-50 px-8 py-6 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Award className="text-purple-600" size={24} />
                <h2 className="text-xl font-black text-slate-800">{t('student.peer_eval')}</h2>
              </div>
              {budget !== null && !isResultsUnlocked && (
                <div className="bg-purple-50 text-purple-700 px-4 py-2 rounded-2xl border border-purple-100 flex items-center gap-2 text-xs font-black uppercase" aria-live="polite">
                  <Award size={16} />
                  {t('student.points_budget')}: {(budget || 0) * teammates.length}
                </div>
              )}
            </div>
            
            <div className="p-8 space-y-12">
              {teammates.map(member => (
                <div key={member.id} className="space-y-6 pb-12 border-b border-slate-100 last:border-0 last:pb-0">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-purple-100 flex items-center justify-center text-purple-700 font-black text-xl">
                        {member.name.charAt(0)}
                      </div>
                      <div>
                        <h3 className="font-black text-slate-800 text-lg">{member.name}</h3>
                        <div className="flex flex-wrap items-center gap-4 mt-1">
                          <a href={`mailto:${member.email}`} className="text-xs font-bold text-slate-400 hover:text-tul-blue transition-colors flex items-center gap-1.5">
                            <Mail size={12} /> {member.email}
                          </a>
                          {member.github_alias && (
                            <>
                              <a href={`https://github.com/${member.github_alias}`} target="_blank" rel="noreferrer" className="text-xs font-bold text-slate-400 hover:text-tul-blue transition-colors flex items-center gap-1.5">
                                <GitHubLogo size={12} /> {member.github_alias}
                              </a>
                              {project.github_url && (
                                <a 
                                  href={`${project.github_url.replace(/\/$/, '')}/pulls?q=is%3Apr+author%3A${member.github_alias}`} 
                                  target="_blank" 
                                  rel="noreferrer" 
                                  className="text-xs font-bold text-slate-400 hover:text-tul-blue transition-colors flex items-center gap-1.5"
                                  title={t('student.view_prs')}
                                >
                                  <GitPullRequest size={12} />
                                  {t('student.view_prs')}
                                </a>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    {budget !== null && (
                      <div className="text-right">
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-1">
                          {t('student.points_allocation')}
                        </span>
                        <span className="text-3xl font-black text-purple-600 leading-none">
                          {peerPoints[member.id] || 0}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="flex items-center gap-2 text-[10px] font-black text-green-700 uppercase tracking-widest">
                        <ThumbsUp size={12} /> {t('student.peer_strengths')}
                      </label>
                      <textarea
                        required
                        disabled={isResultsUnlocked}
                        value={peerTexts[member.id]?.strengths || ''}
                        onChange={(e) => setPeerState({
                          ...peerTexts,
                          [member.id]: { ...(peerTexts[member.id] || { improvements: '' }), strengths: e.target.value }
                        })}
                        className="w-full h-28 p-4 rounded-2xl border border-slate-200 focus:ring-4 focus:ring-purple-500/10 focus:border-purple-500 transition-all bg-slate-50 focus:bg-white resize-none text-sm font-medium disabled:opacity-70"
                        placeholder={t('student.strengths_ph')}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="flex items-center gap-2 text-[10px] font-black text-orange-700 uppercase tracking-widest">
                        <TrendingUp size={12} /> {t('student.peer_improvements')}
                      </label>
                      <textarea
                        required
                        disabled={isResultsUnlocked}
                        value={peerTexts[member.id]?.improvements || ''}
                        onChange={(e) => setPeerState({
                          ...peerTexts,
                          [member.id]: { ...(peerTexts[member.id] || { strengths: '' }), improvements: e.target.value }
                        })}
                        className="w-full h-28 p-4 rounded-2xl border border-slate-200 focus:ring-4 focus:ring-purple-500/10 focus:border-purple-500 transition-all bg-slate-50 focus:bg-white resize-none text-sm font-medium disabled:opacity-70"
                        placeholder={t('student.improvements_ph')}
                      />
                    </div>
                  </div>

                  {budget !== null && (
                    <div className="pt-2 px-2">
                      <input
                        type="range"
                        disabled={isResultsUnlocked}
                        min="0"
                        max={(budget || 0) * 2}
                        step="1"
                        value={peerPoints[member.id] || 0}
                        onChange={(e) => handlePointChange(member.id, Number(e.target.value))}
                        aria-label={`Points for ${member.name}`}
                        className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      />
                      <div className="flex justify-between mt-2 text-[10px] font-black text-slate-300 uppercase tracking-widest">
                        <span>0</span>
                        <span>{budget}</span>
                        <span>{(budget || 0) * 2}</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Footer Actions */}
        {!isResultsUnlocked && (
          <div className="flex flex-col md:flex-row justify-between items-center gap-6 pt-6">
            <div className="flex items-start gap-3 text-slate-400 max-w-md">
              <Info size={20} className="shrink-0 mt-0.5" />
              <p className="text-xs font-medium leading-relaxed italic">
                {t('student.disclaimer')}
              </p>
            </div>
            
            <div className="flex gap-4 w-full md:w-auto">
              <Button
                type="submit"
                disabled={submitting || rating === 0 || remainingPoints !== 0}
                className="w-full md:w-auto rounded-2xl font-bold py-6 px-10 gap-2 shadow-xl shadow-tul-blue/20"
              >
                <Save size={20} />
                {t('profile.save')}
              </Button>
            </div>
          </div>
        )}

        {remainingPoints !== 0 && !isResultsUnlocked && budget !== null && (
          <div className="flex items-center gap-2 text-red-600 bg-red-50 p-4 rounded-2xl border border-red-100 animate-in fade-in slide-in-from-top-2">
            <AlertCircle size={18} />
            <span className="text-sm font-bold">
              {t('student.points_remaining')}: {remainingPoints}. {t('student.points_must_total')} {(budget || 0) * teammates.length}.
            </span>
          </div>
        )}

        {notification && (
          <div className={`flex items-center gap-2 p-4 rounded-2xl border animate-in fade-in ${
            notification.type === 'success'
              ? 'text-green-700 bg-green-50 border-green-100'
              : 'text-red-600 bg-red-50 border-red-100'
          }`}>
            {notification.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
            <span className="text-sm font-bold">{notification.message}</span>
          </div>
        )}
      </form>
    </div>
  );
};
