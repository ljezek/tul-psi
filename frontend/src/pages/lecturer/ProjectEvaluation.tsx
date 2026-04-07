import { useEffect, useState, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router';
import { ArrowLeft, Save, Send, AlertTriangle, Users, XCircle, CheckCircle, Globe } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { getProject, getProjectEvaluation, submitProjectEvaluation, ApiError } from '@/api';
import { ProjectPublic, ProjectEvaluationDetail } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { GitHubLogo } from '@/components/icons/GitHubLogo';

import { ProjectHero } from '@/components/project/ProjectHero';
import { MemberInfo } from '@/components/project/MemberInfo';

export const ProjectEvaluation = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useLanguage();

  const [project, setProject] = useState<ProjectPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [scores, setScores] = useState<Record<string, { score: number | ''; strengths: string; improvements: string }>>({});
  const formRefs = useRef<Record<string, { score: HTMLInputElement | null; strengths: HTMLTextAreaElement | null; improvements: HTMLTextAreaElement | null }>>({});

  useEffect(() => {
    const loadData = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const projectId = parseInt(id, 10);
        
        const projectData = await getProject(projectId);
        setProject(projectData);

        let evalData: ProjectEvaluationDetail | null = null;
        try {
          evalData = await getProjectEvaluation(projectId);
        } catch (err) {
          if (err instanceof ApiError && err.status === 404) {
            evalData = null;
          } else {
            throw err;
          }
        }

        // Initialize form state and refs
        const initialScores: typeof scores = {};
        projectData.course.evaluation_criteria.forEach((c) => {
          const existing = evalData?.scores.find(s => s.criterion_code === c.code);
          initialScores[c.code] = {
            score: existing ? existing.score : '',
            strengths: existing ? existing.strengths : '',
            improvements: existing ? existing.improvements : '',
          };
          formRefs.current[c.code] = { score: null, strengths: null, improvements: null };
        });
        setScores(initialScores);
      } catch (err) {
        if (err instanceof ApiError && typeof err.detail === 'string') {
          setError(err.detail);
        } else {
          setError(t('projectDetail.error_fetching'));
        }
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id, t]);

  const validateForm = () => {
    if (!project) return { valid: false, field: null, message: '' };
    for (const criterion of project.course.evaluation_criteria) {
      const val = scores[criterion.code];
      if (val.score === '' || val.score < 0 || val.score > criterion.max_score) {
        return { 
          valid: false, 
          field: formRefs.current[criterion.code].score, 
          message: `${criterion.description}: ${t('lecturer.error_invalid_score')}` 
        };
      }
      if (!val.strengths.trim()) {
        return { 
          valid: false, 
          field: formRefs.current[criterion.code].strengths, 
          message: `${criterion.description}: ${t('lecturer.error_missing_strengths')}` 
        };
      }
      if (!val.improvements.trim()) {
        return { 
          valid: false, 
          field: formRefs.current[criterion.code].improvements, 
          message: `${criterion.description}: ${t('lecturer.error_missing_improvements')}` 
        };
      }
    }
    return { valid: true, field: null, message: '' };
  };

  const handleSubmit = async (submitFinal: boolean) => {
    if (!project || !id) return;
    
    if (submitFinal) {
      const validation = validateForm();
      if (!validation.valid) {
        alert(validation.message);
        validation.field?.focus();
        validation.field?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
      }
    }

    setSaving(true);
    setError(null);

    const items = project.course.evaluation_criteria.map((c) => {
      const s = scores[c.code];
      return {
        criterion_code: c.code,
        score: s.score === '' ? 0 : Number(s.score),
        strengths: s.strengths.trim(),
        improvements: s.improvements.trim(),
      };
    });

    try {
      await submitProjectEvaluation(parseInt(id, 10), {
        scores: items,
        submitted: submitFinal,
      });
      if (submitFinal) {
        navigate(`/lecturer/course/${project.course.id}`);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          setError(t('lecturer.eval_locked'));
        } else if (err.status === 422) {
          setError(t('lecturer.error_validation'));
        } else if (typeof err.detail === 'string') {
          setError(err.detail);
        } else {
          setError(t('login.error_unexpected'));
        }
      } else {
        setError(t('login.error_unexpected'));
      }
    } finally {
      setSaving(false);
    }
  };

  const handleScoreChange = (code: string, field: 'score' | 'strengths' | 'improvements', value: string | number) => {
    setScores(prev => ({
      ...prev,
      [code]: {
        ...prev[code],
        [field]: value
      }
    }));
  };

  const getScoreColor = (score: number | '', max: number) => {
    if (score === '') return 'text-slate-400';
    const ratio = score / max;
    if (ratio < 0.5) return 'text-red-500';
    if (ratio < 0.75) return 'text-amber-500';
    return 'text-green-500';
  };

  const getBgColor = (score: number | '', max: number) => {
    if (score === '') return 'bg-slate-50 border-slate-100';
    const ratio = score / max;
    if (ratio < 0.5) return 'bg-red-50 border-red-100';
    if (ratio < 0.75) return 'bg-amber-50 border-amber-100';
    return 'bg-green-50 border-green-100';
  };

  if (loading) return <div className="py-20"><LoadingSpinner /></div>;
  if (!project) return <div className="max-w-4xl mx-auto px-4 py-12"><div className="bg-red-50 text-red-600 p-6 rounded-3xl border border-red-100 font-bold">{error || t('projectDetail.not_found')}</div></div>;

  const isReadOnly = Boolean(project.results_unlocked);
  const totalPoints = Object.values(scores).reduce((sum, s) => sum + (Number(s.score) || 0), 0);
  const totalMaxPoints = project.course.evaluation_criteria.reduce((sum, c) => sum + c.max_score, 0);
  const isPass = totalPoints >= project.course.min_score;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8 animate-fade-in">
      <ProjectHero 
        project={project}
        backLink={{ to: `/lecturer/course/${project.course.id}`, label: `${t('lecturer.course_projects')} - ${project.course.code}` }}
        bottomContent={
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
          </div>
        }
        rightContent={
          <div className={`shrink-0 flex items-center gap-4 px-6 py-4 rounded-2xl border ${isPass ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'} transition-colors duration-500`}>
            <div className="text-right">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">
                {t('results.total_score')}
              </span>
              <div className="flex items-baseline gap-1">
                <span className={`text-3xl font-black ${isPass ? 'text-green-600' : 'text-red-600'}`}>
                  {totalPoints}
                </span>
                <span className="text-slate-300 font-bold text-lg">/</span>
                <span className="text-slate-400 font-bold text-lg">{totalMaxPoints}</span>
              </div>
              <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1">
                {t('results.min_required')}: {project.course.min_score}
              </div>
            </div>
            <div className={`p-2 rounded-xl ${isPass ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
              {isPass ? <CheckCircle size={24} /> : <XCircle size={24} />}
            </div>
          </div>
        }
      />

      <div className="bg-white rounded-3xl p-8 border border-slate-200/60 shadow-sm space-y-6">
        <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">{t('project.members')}</h4>
        <MemberInfo members={project.members} variant="grid" />
        
        {isReadOnly && (
          <div className="mt-6 inline-flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-600 rounded-xl border border-amber-100 text-xs font-black uppercase tracking-wider">
            <AlertTriangle size={14} />
            {t('lecturer.eval_locked')}
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-100 text-red-600 p-6 rounded-2xl font-bold flex items-center gap-3">
          <AlertTriangle size={18} />
          {error}
        </div>
      )}

      <div className="space-y-6">
        {project.course.evaluation_criteria.map((criterion) => {
          const val = scores[criterion.code] || { score: '', strengths: '', improvements: '' };
          return (
            <div key={criterion.code} className="bg-white border border-slate-200/60 rounded-3xl p-8 shadow-sm space-y-8">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
                <div className="flex-1">
                  <h3 className="text-xl font-black text-slate-800 mb-2 whitespace-pre-line leading-tight">{criterion.description}</h3>
                </div>
                <div className={`flex items-center gap-4 p-4 rounded-2xl border ${getBgColor(val.score, criterion.max_score)} shrink-0 w-full md:w-auto transition-colors duration-300`}>
                   <div className="flex-1 md:w-32">
                    <input
                      type="range"
                      min="0"
                      max={criterion.max_score}
                      step="1"
                      value={val.score === '' ? 0 : val.score}
                      disabled={isReadOnly}
                      ref={el => { if (formRefs.current[criterion.code]) formRefs.current[criterion.code].score = el; }}
                      onChange={(e) => handleScoreChange(criterion.code, 'score', parseInt(e.target.value, 10))}
                      aria-label={`${criterion.description} - ${t('lecturer.score')}`}
                      className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-tul-blue disabled:opacity-50"
                    />
                    <div className="flex justify-between mt-2 text-[8px] font-black text-slate-300 uppercase tracking-widest">
                      <span>0</span>
                      <span>{criterion.max_score}</span>
                    </div>
                  </div>
                  <div className={`bg-white border border-slate-200 rounded-xl px-3 py-1.5 font-black text-lg min-w-[3rem] text-center shadow-sm ${getScoreColor(val.score, criterion.max_score)} transition-colors duration-300`}>
                    {val.score === '' ? 0 : val.score}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <label className="block text-xs font-black text-green-600 uppercase tracking-widest mb-3 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                    {t('student.label_strengths')}
                  </label>
                  <textarea
                    value={val.strengths}
                    ref={el => { if (formRefs.current[criterion.code]) formRefs.current[criterion.code].strengths = el; }}
                    onChange={(e) => handleScoreChange(criterion.code, 'strengths', e.target.value)}
                    disabled={isReadOnly}
                    rows={4}
                    placeholder={t('lecturer.placeholder_strengths')}
                    aria-label={`${criterion.description} - ${t('student.label_strengths')}`}
                    className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-slate-700 font-medium resize-none focus:bg-white focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 disabled:opacity-70 disabled:bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-black text-amber-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-amber-400" />
                    {t('student.label_improvements')}
                  </label>
                  <textarea
                    value={val.improvements}
                    ref={el => { if (formRefs.current[criterion.code]) formRefs.current[criterion.code].improvements = el; }}
                    onChange={(e) => handleScoreChange(criterion.code, 'improvements', e.target.value)}
                    disabled={isReadOnly}
                    rows={4}
                    placeholder={t('lecturer.placeholder_improvements')}
                    aria-label={`${criterion.description} - ${t('student.label_improvements')}`}
                    className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-slate-700 font-medium resize-none focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 disabled:opacity-70 disabled:bg-slate-50"
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {!isReadOnly && (
        <div className="flex flex-col sm:flex-row justify-end gap-4 pt-6 mt-8 border-t border-slate-200">
          <button
            onClick={() => handleSubmit(false)}
            disabled={saving}
            className="inline-flex items-center justify-center px-6 py-3 bg-white hover:bg-slate-50 text-slate-700 rounded-xl transition-colors border border-slate-200 shadow-sm disabled:opacity-50 font-black text-sm tracking-wide"
          >
            <Save className="w-4 h-4 mr-2 text-slate-400" />
            {t('lecturer.save_draft')}
          </button>
          <button
            onClick={() => handleSubmit(true)}
            disabled={saving}
            className="inline-flex items-center justify-center px-6 py-3 bg-tul-blue hover:bg-tul-blue/90 text-white rounded-xl shadow-sm hover:shadow-tul-blue/20 transition-all duration-300 disabled:opacity-50 font-black text-sm tracking-wide transform hover:-translate-y-0.5"
          >
            <Send className="w-4 h-4 mr-2" />
            {t('lecturer.submit_evaluation')}
          </button>
        </div>
      )}
    </div>
  );
};
