import { useState, useEffect, useMemo, FormEvent } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Star, 
  ThumbsUp, 
  TrendingUp, 
  User, 
  Mail, 
  Send, 
  Save, 
  Info, 
  Award,
  CheckCircle,
  AlertCircle
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

type NotificationState = { type: 'success' | 'error'; message: string } | null;

const StarRating = ({ rating, onChange, disabled }: { rating: number, onChange: (r: number) => void, disabled?: boolean }) => {
  return (
    <div className="flex gap-2">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={disabled}
          aria-label={`Rate ${star}`}
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
  const [isSubmitted, setIsSubmitted] = useState(false);
  
  // Peer state
  const [peerTexts, setPeerState] = useState<Record<number, { strengths: string, improvements: string }>>({});
  // Bonus points loaded from an existing draft; used as the initial distribution.
  const [savedPoints, setSavedPoints] = useState<Record<number, number>>({});

  const teammates = project?.members.filter(m => m.id !== user?.id) || [];
  const budget = project?.course.peer_bonus_budget;

  // Memoize so the object reference is stable between renders. Without this,
  // usePointRedistribution's sync effect would fire every render, creating an
  // infinite loop. savedPoints takes precedence over the equal-split default
  // so that a loaded draft restores the previously saved allocation.
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

      if (evalData) {
        setRating(evalData.rating);
        setStrengths(evalData.strengths);
        setImprovements(evalData.improvements);
        setIsSubmitted(evalData.submitted);
        
        const newPeerTexts: Record<number, { strengths: string, improvements: string }> = {};
        const loadedPoints: Record<number, number> = {};
        evalData.peer_evaluations.forEach(pe => {
          newPeerTexts[pe.receiving_student_id] = {
            strengths: pe.strengths,
            improvements: pe.improvements
          };
          loadedPoints[pe.receiving_student_id] = pe.bonus_points;
        });
        setPeerState(newPeerTexts);
        if (Object.keys(loadedPoints).length > 0) {
          setSavedPoints(loadedPoints);
        }
      }
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

  const handleSubmit = async (e: FormEvent, publish: boolean) => {
    e.preventDefault();
    if (publish && !window.confirm(t('common.confirm_action'))) {
      return;
    }

    setNotification(null);
    setSubmitting(true);
    try {
      const payload: CourseEvaluationSubmit = {
        submitted: publish,
        rating,
        strengths,
        improvements,
        peer_evaluations: teammates.map(m => ({
          receiving_student_id: m.id,
          strengths: peerTexts[m.id]?.strengths || '',
          improvements: peerTexts[m.id]?.improvements || '',
          bonus_points: peerPoints[m.id] || 0
        }))
      };

      await submitCourseEvaluation(projectId, payload);
      if (publish) {
        setIsSubmitted(true);
        navigate('/student');
      } else {
        setNotification({ type: 'success', message: t('student.draft_saved') });
      }
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
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10">
        <Link 
          to="/student"
          className="inline-flex items-center gap-2 text-sm font-bold text-slate-400 hover:text-tul-blue transition-colors mb-6 group"
        >
          <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
          {t('project.back_to_projects')}
        </Link>
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2">
              {t('student.courseEvaluation.title')}
            </h1>
            <p className="text-slate-500 font-medium text-lg">
              {project.title} <span className="text-slate-300 mx-2">|</span> <span className="text-tul-blue">{project.course.code}</span>
            </p>
          </div>
          {isSubmitted && (
            <div className="bg-green-50 text-green-700 px-4 py-2 rounded-2xl border border-green-100 flex items-center gap-2 text-sm font-black uppercase">
              <CheckCircle size={18} />
              {t('student.submitted')}
            </div>
          )}
        </div>
      </div>

      <form onSubmit={(e) => handleSubmit(e, true)} className="space-y-12">
        {/* Subject Evaluation Section */}
        <section className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden">
          <div className="bg-slate-50 px-8 py-6 border-b border-slate-100 flex items-center gap-3">
            <ThumbsUp className="text-tul-blue" size={24} />
            <h2 className="text-xl font-black text-slate-800">{t('student.subject_eval')}</h2>
          </div>
          <div className="p-8 space-y-8">
            <div className="space-y-4">
              <label className="block text-sm font-black text-slate-500 uppercase tracking-widest">{t('student.subject_eval')}</label>
              <StarRating rating={rating} onChange={setRating} disabled={isSubmitted} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-3">
                <label htmlFor="strengths" className="flex items-center gap-2 text-sm font-black text-green-700 uppercase tracking-widest">
                  <ThumbsUp size={16} /> {t('student.subject_strengths')}
                </label>
                <textarea
                  id="strengths"
                  required
                  disabled={isSubmitted}
                  value={strengths}
                  onChange={(e) => setStrengths(e.target.value)}
                  className="w-full h-40 p-4 rounded-2xl border border-slate-200 focus:ring-4 focus:ring-tul-blue/10 focus:border-tul-blue transition-all bg-slate-50 focus:bg-white resize-none text-slate-700 font-medium"
                  placeholder={t('student.strengths_ph')}
                />
              </div>
              <div className="space-y-3">
                <label htmlFor="improvements" className="flex items-center gap-2 text-sm font-black text-orange-700 uppercase tracking-widest">
                  <TrendingUp size={16} /> {t('student.subject_improvements')}
                </label>
                <textarea
                  id="improvements"
                  required
                  disabled={isSubmitted}
                  value={improvements}
                  onChange={(e) => setImprovements(e.target.value)}
                  className="w-full h-40 p-4 rounded-2xl border border-slate-200 focus:ring-4 focus:ring-tul-blue/10 focus:border-tul-blue transition-all bg-slate-50 focus:bg-white resize-none text-slate-700 font-medium"
                  placeholder={t('student.improvements_ph')}
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
                <User className="text-purple-600" size={24} />
                <h2 className="text-xl font-black text-slate-800">{t('student.peer_eval')}</h2>
              </div>
              {budget !== null && !isSubmitted && (
                <div className="bg-purple-50 text-purple-700 px-4 py-2 rounded-2xl border border-purple-100 flex items-center gap-2 text-xs font-black uppercase" aria-live="polite">
                  <Award size={16} />
                  {t('student.points_remaining')}: {remainingPoints}
                </div>
              )}
            </div>
            
            <div className="p-8 space-y-12">
              {teammates.map(member => (
                <div key={member.id} className="space-y-6 pb-12 border-b border-slate-100 last:border-0 last:pb-0">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-purple-100 flex items-center justify-center text-purple-700 font-black text-xl">
                        {member.name.charAt(0)}
                      </div>
                      <div>
                        <h3 className="font-black text-slate-800 text-lg">{member.name}</h3>
                        <div className="flex items-center gap-4 mt-1">
                          <a href={`mailto:${member.email}`} className="text-xs font-bold text-slate-400 hover:text-tul-blue transition-colors flex items-center gap-1.5">
                            <Mail size={12} /> {member.email}
                          </a>
                          {member.github_alias && (
                            <a href={`https://github.com/${member.github_alias}`} target="_blank" rel="noreferrer" className="text-xs font-bold text-slate-400 hover:text-tul-blue transition-colors flex items-center gap-1.5">
                              <GitHubLogo size={12} /> {member.github_alias}
                            </a>
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
                      <textarea
                        required
                        disabled={isSubmitted}
                        value={peerTexts[member.id]?.strengths || ''}
                        onChange={(e) => setPeerState({
                          ...peerTexts,
                          [member.id]: { ...(peerTexts[member.id] || { improvements: '' }), strengths: e.target.value }
                        })}
                        className="w-full h-28 p-4 rounded-2xl border border-slate-200 focus:ring-4 focus:ring-purple-500/10 focus:border-purple-500 transition-all bg-slate-50 focus:bg-white resize-none text-sm font-medium"
                        placeholder={t('student.strengths_ph')}
                      />
                    </div>
                    <div className="space-y-2">
                      <textarea
                        required
                        disabled={isSubmitted}
                        value={peerTexts[member.id]?.improvements || ''}
                        onChange={(e) => setPeerState({
                          ...peerTexts,
                          [member.id]: { ...(peerTexts[member.id] || { strengths: '' }), improvements: e.target.value }
                        })}
                        className="w-full h-28 p-4 rounded-2xl border border-slate-200 focus:ring-4 focus:ring-purple-500/10 focus:border-purple-500 transition-all bg-slate-50 focus:bg-white resize-none text-sm font-medium"
                        placeholder={t('student.improvements_ph')}
                      />
                    </div>
                  </div>

                  {budget !== null && (
                    <div className="pt-2 px-2">
                      <input
                        type="range"
                        disabled={isSubmitted}
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
        {!isSubmitted && (
          <div className="flex flex-col md:flex-row justify-between items-center gap-6 pt-6">
            <div className="flex items-start gap-3 text-slate-400 max-w-md">
              <Info size={20} className="shrink-0 mt-0.5" />
              <p className="text-xs font-medium leading-relaxed italic">
                {t('student.disclaimer')} {t('student.anonymous_notice')}
              </p>
            </div>
            
            <div className="flex gap-4 w-full md:w-auto">
              <Button
                type="button"
                variant="outline"
                disabled={submitting}
                onClick={(e) => handleSubmit(e, false)}
                className="flex-grow md:flex-grow-0 rounded-2xl font-bold py-6 px-8 gap-2 bg-white"
              >
                <Save size={20} />
                {t('profile.save')}
              </Button>
              <Button
                type="submit"
                disabled={submitting || rating === 0 || remainingPoints !== 0}
                className="flex-grow md:flex-grow-0 rounded-2xl font-bold py-6 px-10 gap-2 shadow-xl shadow-tul-blue/20"
              >
                <Send size={20} />
                {t('student.submit')}
              </Button>
            </div>
          </div>
        )}

        {remainingPoints !== 0 && !isSubmitted && budget !== null && (
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
